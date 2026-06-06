# Statement Import Cleanup Checklist

Follow-up cleanup after unifying imports on `StatementImportService`. Use this list so dead code and stale docs do not linger.

**Current source of truth:** [`services/statement_import_service.py`](services/statement_import_service.py) + [`services/statement_file_service.py`](services/statement_file_service.py)

---

## Already removed (Feb 2026 refactor)

- [x] `CSVImportService` / `csv_import_service.py`
- [x] `backend/statement_imports/cards/*` canonicalizers (Amex, BoFA, Chase, Citi, factory, AI-at-import path)

---

## Safe to remove now

### 1. Empty `statement_imports` package

The card import code is gone. Remaining files are unused shells:

```
backend/statement_imports/__init__.py
backend/statement_imports/cards/__init__..py   # typo: double dot in filename
```

**Action:** Delete the entire `backend/statement_imports/` directory.

**Verify:**

```bash
rg "statement_imports" backend/
```

Should return no Python imports (docs may still mention it until updated below).

---

## Docs to update

### 2. Backend guide structure

- **File:** [`backend/CLAUDE.md`](../../CLAUDE.md)
- **Issue:** App tree still lists `statement_imports/`
- **Action:** Remove that entry; point statement import docs at `apps/financial_account/services/statement_import_service.py` and `institutions/registry.py`

### 3. API reference

- **File:** [`API_REFERENCE.md`](../../../API_REFERENCE.md) (repo root)
- **Issue:** Documents `POST /import-csv/` as a primary path
- **Action:** Either remove the row or mark it **deprecated** and note callers should use `POST /import-statement/` with `institution=generic`

---

## Optional — remove only if nothing external uses them

### 4. Legacy `/import-csv/` HTTP route

Kept temporarily for backward compatibility. It now delegates to `StatementImportService` with `institution=generic`.

| Location | What |
|----------|------|
| [`urls.py`](urls.py) | `import-csv/` route |
| [`views.py`](views.py) | `CSVStatementImportAPIView` |

**In-repo usage:** Frontend uses `/import-statement/` only (`frontend/src/lib/api/statementImport.ts`).

**Before deleting:**

```bash
rg "import-csv|account-csv-import|CSVStatementImport" .
```

Check scripts, Postman collections, and any external integrations. If clear, remove route + view and drop the API_REFERENCE row entirely.

**Keep:** Generic CSV tests in `tests/test_csv_import.py` — they already exercise the unified path via `_import_generic()`.

---

### 5. Orphan `DataImporter` utility

Unrelated to statement import, but unused in the app:

| Location | What |
|----------|------|
| [`backend/apps/core/utils/data_importer.py`](../core/utils/data_importer.py) | Bulk CSV seed helper |
| [`backend/apps/core/utils/__init__.py`](../core/utils/__init__.py) | Re-exports `DataImporter` |

**Before deleting:**

```bash
rg "DataImporter|data_importer" backend/
```

Remove only if you are not using it for manual/demo data loads.

---

## Do not remove

| Item | Role |
|------|------|
| `StatementImportService` | Single parse/normalize/dedup/commit engine |
| `StatementFileService` | Drive storage + import orchestration (scanner, UI) |
| `bulk_transaction_service.py` | Fast `bulk_create` + one balance-history pass |
| `institutions/registry.py` | Parser configs + `PARSER_READERS` |
| `institutions/parsers/*` | Format-specific readers (PDF, Amex XLSX, …) |
| `POST /import-statement/` | Primary import API |
| Storage scanner + `scan_statement_storage` command | Auto-import dropped Drive files |

---

## Suggested order

1. Delete `backend/statement_imports/`
2. Update `backend/CLAUDE.md` and `API_REFERENCE.md`
3. Confirm no external `/import-csv/` callers → remove route + view
4. Confirm no `DataImporter` usage → remove utility + export

---

## Validation after cleanup

From `backend/`:

```bash
ruff check .
ruff format --check .
python manage.py check --settings=richtato.test_settings
python -m pytest apps/financial_account/tests/test_csv_import.py apps/financial_account/tests/test_storage_scanner.py -v --tb=short
```
