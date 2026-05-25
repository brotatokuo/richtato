"""Google Drive statement file storage and import orchestration."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from django.core.files.base import File
from django.http import FileResponse
from django.utils import timezone
from django.utils.text import get_valid_filename
from loguru import logger

from apps.financial_account.institutions.registry import supported_extensions_for_parser
from apps.financial_account.models import FinancialAccount, StatementFile
from apps.financial_account.services.statement_import_service import StatementImportResult, StatementImportService
from apps.financial_account.storage import UnknownStorageScheme, get_storage
from apps.richtato_user.models import User


@dataclass
class StatementUploadResult:
    """Result of saving an uploaded statement into Google Drive."""

    statement: StatementFile
    created: bool


class StatementFileService:
    """Manage Google Drive statement files and import history."""

    SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
    STATEMENT_PERIOD_MAX_LENGTH = 40

    def __init__(self):
        self.import_service = StatementImportService()

    def list_statements(
        self,
        user: User,
        account_id: int | None = None,
        year: int | None = None,
        month: int | None = None,
        institution: str | None = None,
        import_status: str | None = None,
    ):
        """List active statement files for a user with optional folder filters."""
        if account_id:
            account = FinancialAccount.objects.filter(id=account_id, user=user).first()
            if account:
                self.reconcile_missing_storage(account)

        queryset = StatementFile.objects.filter(user=user, is_deleted=False).select_related("account")
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        if year:
            queryset = queryset.filter(statement_year=year)
        if month:
            queryset = queryset.filter(statement_month=month)
        if institution:
            queryset = queryset.filter(institution=institution)
        if import_status:
            queryset = queryset.filter(import_status=import_status)
        return queryset

    def get_statement(self, user: User, statement_id: int) -> StatementFile | None:
        """Fetch a non-deleted statement owned by the user."""
        return (
            StatementFile.objects.select_related("account").filter(id=statement_id, user=user, is_deleted=False).first()
        )

    def save_upload(
        self,
        user: User,
        account: FinancialAccount,
        uploaded_file,
        institution: str,
        statement_period: str = "",
        statement_status: str = "provisional",
        statement_year: int | None = None,
        statement_month: int | None = None,
        source: str = "manual_upload",
    ) -> StatementUploadResult:
        """Save an uploaded statement to the account's Google Drive folder."""
        filename = get_valid_filename(Path(uploaded_file.name).name)
        extension = Path(filename).suffix.lower()
        allowed_extensions = supported_extensions_for_parser(institution)
        if extension not in allowed_extensions:
            raise ValueError(
                f"Unsupported file type for this account. Allowed extensions: {', '.join(sorted(allowed_extensions))}."
            )

        self._validate_statement_period(statement_period)

        content = uploaded_file.read()
        if isinstance(content, str):
            content = content.encode()
        file_hash = hashlib.sha256(content).hexdigest()
        year, month = self._resolve_year_month(statement_period, statement_year, statement_month)

        existing = (
            StatementFile.objects.filter(
                user=user,
                account=account,
                file_hash=file_hash,
                is_deleted=False,
            )
            .select_related("account")
            .first()
        )
        if existing:
            updated_fields: list[str] = []
            if existing.institution != institution:
                existing.institution = institution
                updated_fields.append("institution")
            if statement_period and existing.statement_period != statement_period:
                existing.statement_period = statement_period
                updated_fields.append("statement_period")
            if existing.statement_year != year:
                existing.statement_year = year
                updated_fields.append("statement_year")
            if existing.statement_month != month:
                existing.statement_month = month
                updated_fields.append("statement_month")
            if existing.statement_status != statement_status:
                existing.statement_status = statement_status
                updated_fields.append("statement_status")
            if updated_fields:
                updated_fields.append("updated_at")
                existing.save(update_fields=updated_fields)
            return StatementUploadResult(statement=existing, created=False)

        storage_uri = account.ensure_storage_uri()
        storage = get_storage(storage_uri)
        relative_path = self._build_relative_path(file_hash, filename)
        stored = storage.write_file(storage_uri, relative_path, content)
        drive_file_id = stored.external_file_id or self._lookup_drive_file_id(
            account,
            self._stored_path_from_storage(storage_uri, stored.relative_path),
        )

        statement = StatementFile.objects.create(
            user=user,
            account=account,
            institution=institution,
            statement_period=statement_period,
            statement_year=year,
            statement_month=month,
            statement_status=statement_status,
            import_status="uploaded",
            original_filename=filename,
            stored_path=self._stored_path_from_storage(storage_uri, stored.relative_path),
            drive_file_id=drive_file_id,
            content_type=getattr(uploaded_file, "content_type", "") or "",
            size_bytes=len(content),
            file_hash=file_hash,
            source=source,
        )
        logger.info("Stored statement file", statement_id=statement.id, account_id=account.id)
        return StatementUploadResult(statement=statement, created=True)

    def register_discovered_file_and_import(
        self,
        *,
        account: FinancialAccount,
        stored_path: str,
        original_filename: str,
        file_hash: str,
        size_bytes: int,
        drive_file_id: str,
        institution: str,
        statement_period: str,
        statement_year: int,
        statement_month: int,
        source: str = "agent_drop",
    ) -> tuple[StatementFile, StatementImportResult]:
        """Catalog an already-stored file and auto-import its transactions."""
        statement = StatementFile.objects.create(
            user=account.user,
            account=account,
            institution=institution,
            statement_period=statement_period,
            statement_year=statement_year,
            statement_month=statement_month,
            statement_status="provisional",
            import_status="uploaded",
            original_filename=original_filename,
            stored_path=stored_path,
            drive_file_id=drive_file_id,
            content_type="",
            size_bytes=size_bytes,
            file_hash=file_hash,
            source=source,
        )
        result = self.import_statement(statement)
        return statement, result

    def update_statement(
        self,
        statement: StatementFile,
        account: FinancialAccount | None = None,
        institution: str | None = None,
        statement_period: str | None = None,
        statement_status: str | None = None,
        statement_year: int | None = None,
        statement_month: int | None = None,
    ) -> StatementFile:
        """Update metadata and move the stored file when account changes."""
        if statement_period is not None:
            self._validate_statement_period(statement_period)

        old_account = statement.account
        old_storage_uri = old_account.ensure_storage_uri()
        old_relative = self._stored_relative_path(statement.stored_path, old_storage_uri)
        new_account = account or statement.account
        new_period = statement.statement_period if statement_period is None else statement_period
        year_override = statement_year
        month_override = statement_month
        if statement_period is None:
            year_override = statement.statement_year if year_override is None else year_override
            month_override = statement.statement_month if month_override is None else month_override
        year, month = self._resolve_year_month(
            new_period,
            year_override,
            month_override,
        )

        if account is not None:
            statement.account = account
        if institution is not None:
            statement.institution = institution
        if statement_period is not None:
            statement.statement_period = statement_period
        if statement_status is not None:
            statement.statement_status = statement_status
        statement.statement_year = year
        statement.statement_month = month

        new_storage_uri = new_account.ensure_storage_uri()
        new_relative = self._build_relative_path(statement.file_hash, statement.original_filename)

        if new_storage_uri == old_storage_uri:
            if old_relative != new_relative:
                storage = get_storage(new_storage_uri)
                storage.move_file(new_storage_uri, old_relative, new_relative)
                statement.stored_path = self._stored_path_from_storage(new_storage_uri, new_relative)
        else:
            old_storage = get_storage(old_storage_uri)
            with old_storage.open_file(old_storage_uri, old_relative) as handle:
                content = handle.read()
            new_storage = get_storage(new_storage_uri)
            new_storage.write_file(new_storage_uri, new_relative, content)
            try:
                old_storage.delete_file(old_storage_uri, old_relative)
            except Exception:
                logger.exception("Failed to remove statement file after move")
            statement.stored_path = self._stored_path_from_storage(new_storage_uri, new_relative)

        statement.save()
        return statement

    def acknowledge_reconciliation(self, statement: StatementFile) -> StatementFile:
        """Mark current reconciliation warnings as reviewed by the user."""
        warnings = (statement.last_import_result or {}).get("reconciliation_warnings") or []
        if not warnings:
            raise ValueError("No reconciliation warnings to acknowledge")
        statement.reconciliation_acknowledged_at = timezone.now()
        statement.save(update_fields=["reconciliation_acknowledged_at", "updated_at"])
        return statement

    def soft_delete_statement(self, statement: StatementFile) -> None:
        """Remove the stored file when present and soft-delete the catalog row."""
        try:
            storage_uri = statement.account.ensure_storage_uri()
            relative = self._stored_relative_path(statement.stored_path, storage_uri)
            storage = get_storage(storage_uri)
            storage.delete_file(storage_uri, relative)
        except Exception:
            logger.exception(
                "Failed to delete stored statement file before soft delete",
                statement_id=statement.id,
                stored_path=statement.stored_path,
            )
        statement.soft_delete()

    def reconcile_missing_storage(
        self,
        account: FinancialAccount,
        *,
        present_relative_paths: set[str] | None = None,
    ) -> int:
        """Soft-delete statement rows whose Google Drive file no longer exists."""
        storage_uri = account.resolved_storage_uri()
        if not storage_uri:
            return 0

        if present_relative_paths is None:
            try:
                storage = get_storage(storage_uri)
                present_relative_paths = {stored.relative_path for stored in storage.list_files(storage_uri)}
            except (NotImplementedError, UnknownStorageScheme, ValueError) as exc:
                logger.warning(
                    "Skipping statement storage reconcile for account {}: {}",
                    account.id,
                    exc,
                )
                return 0

        removed = 0
        for statement in StatementFile.objects.filter(account=account, is_deleted=False):
            relative = self._stored_relative_path(statement.stored_path, storage_uri)
            if relative in present_relative_paths:
                continue
            statement.soft_delete()
            removed += 1
            logger.info(
                "Removed orphaned statement catalog row",
                account_id=account.id,
                statement_id=statement.id,
                stored_path=statement.stored_path,
            )
        return removed

    def download_response(self, statement: StatementFile) -> FileResponse:
        """Return a file response for a stored statement."""
        handle = self._open_stored_file(statement)
        return FileResponse(
            handle,
            as_attachment=True,
            filename=statement.original_filename,
            content_type=statement.content_type or "application/octet-stream",
        )

    def preview_statement(self, statement: StatementFile) -> StatementImportResult:
        """Run import preview against the stored file and persist the summary."""
        result = self._run_import(statement, commit=False)
        self._update_import_summary(statement, result, "previewed")
        return result

    def import_statement(
        self,
        statement: StatementFile,
        *,
        apply_opening_balance: bool = False,
    ) -> StatementImportResult:
        """Commit import from the stored file and persist the summary."""
        result = self._run_import(statement, commit=True, apply_opening_balance=apply_opening_balance)
        import_status = (
            "failed" if result.errors and result.imported_count == 0 and result.parsed_count == 0 else "imported"
        )
        self._update_import_summary(statement, result, import_status)
        return result

    def serialize(self, statement: StatementFile) -> dict[str, Any]:
        """Serialize a statement file for API responses."""
        return {
            "id": statement.id,
            "account": statement.account_id,
            "account_name": statement.account.name,
            "institution": statement.institution,
            "statement_period": statement.statement_period,
            "statement_year": statement.statement_year,
            "statement_month": statement.statement_month,
            "statement_status": statement.statement_status,
            "import_status": statement.import_status,
            "original_filename": statement.original_filename,
            "content_type": statement.content_type,
            "size_bytes": statement.size_bytes,
            "file_hash": statement.file_hash,
            "parsed_count": statement.parsed_count,
            "imported_count": statement.imported_count,
            "duplicate_count": statement.duplicate_count,
            "invalid_count": statement.invalid_count,
            "possible_changed_count": statement.possible_changed_count,
            "last_import_result": statement.last_import_result,
            "reconciliation_acknowledged_at": (
                statement.reconciliation_acknowledged_at.isoformat()
                if statement.reconciliation_acknowledged_at
                else None
            ),
            "source": statement.source,
            "stored_path": statement.stored_path,
            "drive_file_url": self._drive_file_view_url(statement),
            "created_at": statement.created_at.isoformat(),
            "updated_at": statement.updated_at.isoformat(),
        }

    def build_folder_tree(self, statements) -> list[dict[str, Any]]:
        """Build account -> year -> month folders from statement rows."""
        accounts: dict[int, dict[str, Any]] = {}
        for statement in statements:
            account_node = accounts.setdefault(
                statement.account_id,
                {
                    "account_id": statement.account_id,
                    "account_name": statement.account.name,
                    "years": {},
                    "count": 0,
                },
            )
            account_node["count"] += 1
            year_node = account_node["years"].setdefault(
                statement.statement_year,
                {"year": statement.statement_year, "months": {}, "count": 0},
            )
            year_node["count"] += 1
            month_node = year_node["months"].setdefault(
                statement.statement_month,
                {"month": statement.statement_month, "count": 0},
            )
            month_node["count"] += 1

        tree = []
        for account_node in accounts.values():
            years = []
            for year_node in sorted(account_node["years"].values(), key=lambda item: item["year"], reverse=True):
                months = sorted(year_node["months"].values(), key=lambda item: item["month"], reverse=True)
                years.append({**year_node, "months": months})
            tree.append({**account_node, "years": years})
        return sorted(tree, key=lambda item: item["account_name"].lower())

    def _open_stored_file(self, statement: StatementFile):
        """Return an open ``BinaryIO`` for a stored statement."""
        storage_uri = statement.account.ensure_storage_uri()
        relative = self._stored_relative_path(statement.stored_path, storage_uri)
        storage = get_storage(storage_uri)
        return storage.open_file(storage_uri, relative)

    def _run_import(
        self,
        statement: StatementFile,
        commit: bool,
        *,
        apply_opening_balance: bool = False,
    ) -> StatementImportResult:
        with self._open_stored_file(statement) as stored_file:
            django_file = File(stored_file, name=statement.original_filename)
            if commit:
                return self.import_service.import_statement(
                    statement.account,
                    django_file,
                    statement.institution,
                    statement.statement_period,
                    statement.statement_status,
                    apply_opening_balance=apply_opening_balance,
                )
            return self.import_service.preview_statement(
                statement.account,
                django_file,
                statement.institution,
                statement.statement_period,
                statement.statement_status,
            )

    def _update_import_summary(
        self,
        statement: StatementFile,
        result: StatementImportResult,
        import_status: str,
    ) -> None:
        statement.parsed_count = result.parsed_count
        statement.imported_count = result.imported_count
        statement.duplicate_count = result.duplicate_count
        statement.invalid_count = result.invalid_count
        statement.possible_changed_count = result.possible_changed_count
        statement.last_import_result = result.as_dict()
        statement.import_status = import_status
        if result.reconciliation_warnings:
            statement.reconciliation_acknowledged_at = None
        statement.save(
            update_fields=[
                "parsed_count",
                "imported_count",
                "duplicate_count",
                "invalid_count",
                "possible_changed_count",
                "last_import_result",
                "import_status",
                "reconciliation_acknowledged_at",
                "updated_at",
            ]
        )

    def _validate_statement_period(self, statement_period: str) -> None:
        if len(statement_period) > self.STATEMENT_PERIOD_MAX_LENGTH:
            raise ValueError(f"statement_period must be {self.STATEMENT_PERIOD_MAX_LENGTH} characters or fewer")

    def _resolve_year_month(
        self,
        statement_period: str,
        statement_year: int | None,
        statement_month: int | None,
    ) -> tuple[int, int]:
        if statement_year and statement_month:
            self._validate_month(statement_month)
            return int(statement_year), int(statement_month)

        match = re.search(r"(?P<year>\d{4})[-/ ](?P<month>\d{1,2})", statement_period or "")
        if match:
            month = int(match.group("month"))
            self._validate_month(month)
            return int(match.group("year")), month

        today = date.today()
        return today.year, today.month

    def _validate_month(self, month: int) -> None:
        if month < 1 or month > 12:
            raise ValueError("statement_month must be between 1 and 12")

    def _build_relative_path(self, file_hash: str, filename: str) -> str:
        """Build the flat Drive filename for a statement file."""
        safe_filename = get_valid_filename(filename)
        return f"{file_hash[:12]}-{safe_filename}"

    def _stored_path_from_storage(self, storage_uri: str, relative_path: str) -> str:
        """Compose a ``StatementFile.stored_path`` that round-trips through Drive."""
        return f"{storage_uri.rstrip('/')}/{relative_path}"

    def _stored_relative_path(self, stored_path: str, storage_uri: str) -> str:
        """Compute the Drive filename from a stored row."""
        prefix = storage_uri.rstrip("/") + "/"
        if stored_path.startswith(prefix):
            return stored_path[len(prefix) :]
        return Path(stored_path).name

    def _lookup_drive_file_id(self, account: FinancialAccount, stored_path: str) -> str:
        """Resolve a Drive file id from a stored gdrive:// path."""
        if not stored_path.startswith("gdrive://"):
            return ""
        try:
            parsed = urlparse(stored_path)
            folder_id = parsed.netloc
            filename = Path(parsed.path.lstrip("/")).name
            if not folder_id or not filename:
                return ""

            storage_uri = f"gdrive://{folder_id}"
            storage = get_storage(storage_uri)
            from apps.financial_account.storage.gdrive import GoogleDriveStatementStorage

            if not isinstance(storage, GoogleDriveStatementStorage):
                return ""
            connection = storage.drive.connection_for_folder(folder_id)
            return storage.drive.file_id_for_name(connection, folder_id, filename)
        except Exception:
            logger.exception("Failed to resolve Drive file id", stored_path=stored_path, account_id=account.id)
            return ""

    def _drive_file_view_url(self, statement: StatementFile) -> str | None:
        """Return a browser URL for the stored Drive file when available."""
        file_id = statement.drive_file_id
        if not file_id:
            file_id = self._lookup_drive_file_id(statement.account, statement.stored_path)
            if file_id:
                statement.drive_file_id = file_id
                statement.save(update_fields=["drive_file_id", "updated_at"])
        if not file_id:
            return None
        from apps.financial_account.services.google_drive_service import GoogleDriveService

        return GoogleDriveService.file_view_url(file_id)
