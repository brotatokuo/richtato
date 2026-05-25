# Bank connector specs

Drop sample statement exports here when building parsers or download adapters.
One folder per institution + account type; any reasonable filename is fine.

## Scope

| Institution | Account types |
| --- | --- |
| Bank of America | `checking/`, `savings/`, `credit_card/` |
| American Express | `checking/`, `credit_card/` |
| Chase | `checking/`, `savings/`, `credit_card/` |
| Citi | `credit_card/` |
| Marcus | `savings/` |

## Folder layout

```text
connector-specs/
├── README.md
├── bofa/checking/
├── bofa/savings/
├── bofa/credit_card/
├── amex/checking/
├── amex/credit_card/
├── chase/checking/
├── chase/savings/
├── chase/credit_card/
├── citi/credit_card/          ← citi_costco.csv
└── marcus/savings/
```

Add 1–2 real exports per folder (`activity-export.csv`, `activity-export.xlsx`, or a
descriptive name like `citi_costco.csv`). Redact account numbers if you want; keep
headers and row structure.

Mention quirks in chat (PDF-only, separate Debit/Credit columns, header row number,
amount sign convention) — no per-folder README required.

## Implementation status

| Institution | Type | Parser | Download adapter |
| --- | --- | --- | --- |
| BoFA | Checking | Done | Done |
| BoFA | Savings | Partial | Done |
| BoFA | Credit | Partial | Done |
| Amex | Checking | Needed | Needed (PDF not supported yet) |
| Amex | Credit | Partial | Needed |
| Chase | Checking | Done | Done |
| Chase | Savings | Partial | Done |
| Chase | Credit | Partial | Done |
| Citi | Credit | Done | Needed |
| Marcus | Savings | Partial | Needed |

**Parser** → `backend/apps/financial_account/services/statement_import_service.py`
**Download adapter** → `scripts/bank_sync/institutions/`

Parsers can ship before Playwright automation (manual upload / Drive drop works first).

## Agent `flow` mapping

| Account types | Agent `flow` |
| --- | --- |
| Checking, Savings | `deposit` |
| Credit | `credit_card` |
