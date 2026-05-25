"""Discover and auto-import statement files in Google Drive account folders.

Walks each account's ``gdrive://`` storage URI looking for files that are
not yet tracked in ``StatementFile``. New files become ``agent_drop`` rows
and are auto-imported via :class:`StatementImportService`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from django.core.files.base import ContentFile
from loguru import logger

from apps.financial_account.models import FinancialAccount, StatementFile
from apps.financial_account.services.statement_file_service import StatementFileService
from apps.financial_account.services.statement_import_service import StatementImportResult, StatementImportService
from apps.financial_account.storage import UnknownStorageScheme, get_storage

# FinancialInstitution.slug -> StatementImportService parser key. Slugs that
# already match the parser key (chase, marcus, amex, fidelity, guideline)
# fall through and are used verbatim.
INSTITUTION_SLUG_TO_PARSER = {
    "bank_of_america": "bofa",
    "citibank": "citi",
    "robinhood": "robinhood_bank",
    "robinhood_investments": "robinhood_investments",
    "robinhood_bank": "robinhood_bank",
}


def parser_key_for_account(account: FinancialAccount) -> str | None:
    """Map an account's institution slug to a StatementImportService parser key."""
    institution = account.institution
    if institution is None:
        return None
    slug = (institution.slug or "").lower()
    if not slug:
        return None
    if slug in INSTITUTION_SLUG_TO_PARSER:
        return INSTITUTION_SLUG_TO_PARSER[slug]
    from apps.financial_account.services.statement_import_service import SUPPORTED_INSTITUTIONS

    if slug in SUPPORTED_INSTITUTIONS:
        return slug
    return None


@dataclass
class ScanFileOutcome:
    """Per-file scan outcome (one entry per file inspected)."""

    account_id: int
    relative_path: str
    status: str  # discovered | skipped_duplicate | skipped_unsupported | imported | failed
    detail: str = ""
    imported_count: int = 0


@dataclass
class ScanResult:
    """Aggregate counts for a single scan run."""

    accounts_scanned: int = 0
    files_seen: int = 0
    files_imported: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    files_removed: int = 0
    outcomes: list[ScanFileOutcome] = field(default_factory=list)


class StorageScannerService:
    """Discover dropped statement files and auto-import them."""

    SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}

    def __init__(self):
        self.import_service = StatementImportService()
        self.statement_file_service = StatementFileService()

    def scan_all(self, *, dry_run: bool = False) -> ScanResult:
        """Scan every active FinancialAccount for new files."""
        return self._scan(FinancialAccount.objects.filter(is_active=True), dry_run=dry_run)

    def scan_user(self, user_id: int, *, dry_run: bool = False) -> ScanResult:
        """Scan only the active accounts owned by ``user_id``."""
        return self._scan(
            FinancialAccount.objects.filter(user_id=user_id, is_active=True),
            dry_run=dry_run,
        )

    def scan_account(self, account_id: int, *, dry_run: bool = False) -> ScanResult:
        """Scan a single account by id."""
        return self._scan(FinancialAccount.objects.filter(id=account_id), dry_run=dry_run)

    def _scan(self, accounts: Iterable[FinancialAccount], *, dry_run: bool) -> ScanResult:
        result = ScanResult()
        for account in accounts.select_related("institution", "user"):
            result.accounts_scanned += 1
            self._scan_account(account, result, dry_run=dry_run)
        logger.info(
            "Storage scan complete: accounts={} files_seen={} imported={} skipped={} failed={} removed={} dry_run={}",
            result.accounts_scanned,
            result.files_seen,
            result.files_imported,
            result.files_skipped,
            result.files_failed,
            result.files_removed,
            dry_run,
        )
        return result

    def _scan_account(self, account: FinancialAccount, result: ScanResult, *, dry_run: bool) -> None:
        storage_uri = account.resolved_storage_uri()
        if not storage_uri:
            logger.warning(
                "Skipping account {} ({}): Google Drive storage is not configured",
                account.id,
                account.name,
            )
            return
        try:
            storage = get_storage(storage_uri)
        except (NotImplementedError, UnknownStorageScheme, ValueError) as exc:
            logger.warning(
                "Skipping account {} ({}): storage backend unavailable: {}",
                account.id,
                storage_uri,
                exc,
            )
            return

        try:
            stored_files = list(storage.list_files(storage_uri))
        except ValueError as exc:
            logger.warning(
                "Skipping account {} ({}): could not list storage files: {}",
                account.id,
                storage_uri,
                exc,
            )
            result.files_failed += 1
            result.outcomes.append(
                ScanFileOutcome(
                    account_id=account.id,
                    relative_path="",
                    status="failed",
                    detail=str(exc),
                )
            )
            return

        if not dry_run:
            present_paths = {stored.relative_path for stored in stored_files}
            result.files_removed += self.statement_file_service.reconcile_missing_storage(
                account,
                present_relative_paths=present_paths,
            )

        parser_key = self._parser_key_for_account(account)
        for stored in stored_files:
            result.files_seen += 1
            if Path(stored.filename).suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                result.files_skipped += 1
                result.outcomes.append(
                    ScanFileOutcome(
                        account_id=account.id,
                        relative_path=stored.relative_path,
                        status="skipped_unsupported",
                        detail=f"Extension not supported: {stored.filename}",
                    )
                )
                continue

            file_hash = storage.file_hash(storage_uri, stored.relative_path)
            existing = StatementFile.objects.filter(
                account=account,
                file_hash=file_hash,
                is_deleted=False,
            ).first()
            if existing:
                result.files_skipped += 1
                result.outcomes.append(
                    ScanFileOutcome(
                        account_id=account.id,
                        relative_path=stored.relative_path,
                        status="skipped_duplicate",
                        detail=f"statement_file={existing.id}",
                    )
                )
                continue

            if dry_run:
                result.outcomes.append(
                    ScanFileOutcome(
                        account_id=account.id,
                        relative_path=stored.relative_path,
                        status="discovered",
                        detail=f"hash={file_hash[:12]}",
                    )
                )
                continue

            if not parser_key:
                result.files_failed += 1
                result.outcomes.append(
                    ScanFileOutcome(
                        account_id=account.id,
                        relative_path=stored.relative_path,
                        status="failed",
                        detail=(
                            "No parser configured for institution "
                            f"{account.institution.slug if account.institution else 'manual'!r}"
                        ),
                    )
                )
                continue

            try:
                self._import_one(
                    account=account,
                    storage_uri=storage_uri,
                    storage=storage,
                    stored=stored,
                    file_hash=file_hash,
                    parser_key=parser_key,
                    result=result,
                )
            except Exception as exc:
                logger.exception("Storage scan import failed account={} path={}", account.id, stored.relative_path)
                result.files_failed += 1
                result.outcomes.append(
                    ScanFileOutcome(
                        account_id=account.id,
                        relative_path=stored.relative_path,
                        status="failed",
                        detail=str(exc),
                    )
                )

    def _import_one(
        self,
        *,
        account: FinancialAccount,
        storage_uri: str,
        storage,
        stored,
        file_hash: str,
        parser_key: str,
        result: ScanResult,
    ) -> None:
        year, month = self._year_month_from_path(stored.relative_path)
        with storage.open_file(storage_uri, stored.relative_path) as handle:
            content = handle.read()

        statement = StatementFile.objects.create(
            user=account.user,
            account=account,
            institution=parser_key,
            statement_period=f"{year}-{month:02d}",
            statement_year=year,
            statement_month=month,
            statement_status="provisional",
            import_status="uploaded",
            original_filename=stored.filename,
            stored_path=self._stored_path_from_storage(storage_uri, stored.relative_path),
            drive_file_id=getattr(stored, "external_file_id", "") or "",
            content_type="",
            size_bytes=stored.size_bytes,
            file_hash=file_hash,
            source="agent_drop",
        )

        django_file = ContentFile(content, name=stored.filename)
        import_result: StatementImportResult = self.import_service.import_statement(
            account=account,
            statement_file=django_file,
            institution=parser_key,
            statement_period=statement.statement_period,
            statement_status="provisional",
        )

        import_status = "imported"
        if import_result.errors and import_result.imported_count == 0 and import_result.parsed_count == 0:
            import_status = "failed"

        statement.parsed_count = import_result.parsed_count
        statement.imported_count = import_result.imported_count
        statement.duplicate_count = import_result.duplicate_count
        statement.invalid_count = import_result.invalid_count
        statement.possible_changed_count = import_result.possible_changed_count
        statement.last_import_result = import_result.as_dict()
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

        if import_status == "failed":
            result.files_failed += 1
            result.outcomes.append(
                ScanFileOutcome(
                    account_id=account.id,
                    relative_path=stored.relative_path,
                    status="failed",
                    detail=", ".join(import_result.errors)[:240],
                )
            )
            return

        result.files_imported += 1
        result.outcomes.append(
            ScanFileOutcome(
                account_id=account.id,
                relative_path=stored.relative_path,
                status="imported",
                detail=f"statement_file={statement.id}",
                imported_count=import_result.imported_count,
            )
        )

    def _parser_key_for_account(self, account: FinancialAccount) -> str | None:
        return parser_key_for_account(account)

    def _year_month_from_path(self, relative_path: str) -> tuple[int, int]:
        """Pull ``year`` / ``month`` from ``<year>/<month>/...`` paths; fall back to today."""
        match = re.match(r"(?P<year>\d{4})/(?P<month>\d{2})/", relative_path)
        if match:
            return int(match.group("year")), int(match.group("month"))
        today = date.today()
        return today.year, today.month

    def _stored_path_from_storage(self, storage_uri: str, relative_path: str) -> str:
        """Compose a StatementFile.stored_path that round-trips through Drive."""
        return f"{storage_uri.rstrip('/')}/{relative_path}"
