"""Local statement file storage and import orchestration."""

from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import File
from django.http import FileResponse
from django.utils.text import get_valid_filename
from loguru import logger

from apps.financial_account.models import FinancialAccount, StatementFile
from apps.financial_account.services.statement_import_service import StatementImportResult, StatementImportService
from apps.richtato_user.models import User


@dataclass
class StatementUploadResult:
    """Result of saving an uploaded statement into the local library."""

    statement: StatementFile
    created: bool


class StatementFileService:
    """Manage locally stored statement files and import history."""

    SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}

    def __init__(self):
        self.import_service = StatementImportService()
        self.storage_root = settings.BASE_DIR.parent / "local_data" / "statements"

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
    ) -> StatementUploadResult:
        """Save an uploaded statement into the account/year/month local folder."""
        filename = get_valid_filename(Path(uploaded_file.name).name)
        extension = Path(filename).suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file type. Upload a CSV, XLS, or XLSX file.")

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
            return StatementUploadResult(statement=existing, created=False)

        target_path = self._build_storage_path(user.id, account.id, year, month, file_hash, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

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
            stored_path=self._relative_path(target_path),
            content_type=getattr(uploaded_file, "content_type", "") or "",
            size_bytes=len(content),
            file_hash=file_hash,
        )
        logger.info("Stored statement file", statement_id=statement.id, account_id=account.id)
        return StatementUploadResult(statement=statement, created=True)

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
        """Update metadata and move the local file when account/period changes."""
        old_path = self._absolute_path(statement.stored_path)
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

        new_path = self._build_storage_path(
            statement.user_id,
            new_account.id,
            year,
            month,
            statement.file_hash,
            statement.original_filename,
        )
        if old_path != new_path:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
            statement.stored_path = self._relative_path(new_path)

        statement.save()
        return statement

    def soft_delete_statement(self, statement: StatementFile) -> None:
        """Soft delete the statement record without removing local history immediately."""
        statement.soft_delete()

    def download_response(self, statement: StatementFile) -> FileResponse:
        """Return a file response for a stored statement."""
        path = self._absolute_path(statement.stored_path)
        if not path.exists():
            raise FileNotFoundError("Stored statement file not found")
        return FileResponse(
            path.open("rb"),
            as_attachment=True,
            filename=statement.original_filename,
            content_type=statement.content_type or "application/octet-stream",
        )

    def preview_statement(self, statement: StatementFile) -> StatementImportResult:
        """Run import preview against the stored file and persist the summary."""
        result = self._run_import(statement, commit=False)
        self._update_import_summary(statement, result, "previewed")
        return result

    def import_statement(self, statement: StatementFile) -> StatementImportResult:
        """Commit import from the stored file and persist the summary."""
        result = self._run_import(statement, commit=True)
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

    def _run_import(self, statement: StatementFile, commit: bool) -> StatementImportResult:
        path = self._absolute_path(statement.stored_path)
        if not path.exists():
            raise FileNotFoundError("Stored statement file not found")
        with path.open("rb") as stored_file:
            django_file = File(stored_file, name=statement.original_filename)
            if commit:
                return self.import_service.import_statement(
                    statement.account,
                    django_file,
                    statement.institution,
                    statement.statement_period,
                    statement.statement_status,
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
        statement.save(
            update_fields=[
                "parsed_count",
                "imported_count",
                "duplicate_count",
                "invalid_count",
                "possible_changed_count",
                "last_import_result",
                "import_status",
                "updated_at",
            ]
        )

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

    def _build_storage_path(
        self,
        user_id: int,
        account_id: int,
        year: int,
        month: int,
        file_hash: str,
        filename: str,
    ) -> Path:
        safe_filename = get_valid_filename(filename)
        return (
            self.storage_root
            / str(user_id)
            / str(account_id)
            / str(year)
            / f"{month:02d}"
            / f"{file_hash[:12]}-{safe_filename}"
        )

    def _relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(settings.BASE_DIR.parent))
        except ValueError:
            return str(path)

    def _absolute_path(self, stored_path: str) -> Path:
        path = Path(stored_path)
        if path.is_absolute():
            return path
        return settings.BASE_DIR.parent / path
