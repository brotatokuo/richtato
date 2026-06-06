# Bank connector specs

Drop sample statement exports here when building statement parsers.
One folder per institution + account type; any reasonable filename is fine.

## Scope

| Institution | Account types |
| --- | --- |
| Bank of America | `checking/`, `savings/`, `credit_card/` |
| American Express | `checking/`, `credit_card/` |
| Chase | `checking/`, `savings/`, `credit_card/` |
| Citi | `credit_card/` |
| Marcus | `savings/` |
| Robinhood | `checking/`, `savings/`, `credit_card/` |
| Guideline | `investment/` |

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
├── marcus/savings/
├── robinhood/checking/        ← robinhood_checking_april_2026.pdf
└── robinhood/credit_card/     ← robinhood_credit_may_2026.pdf
```

Add 1–2 real exports per folder (`activity-export.csv`, `activity-export.xlsx`, a
descriptive name like `citi_costco.csv`, or a monthly PDF such as
`robinhood_credit_may_2026.pdf`). Redact account numbers if you want; keep
headers and row structure.

Mention quirks in chat (PDF-only, separate Debit/Credit columns, header row number,
amount sign convention) — no per-folder README required.

## Implementation status

| Institution | Type | Parser |
| --- | --- | --- |
| BoFA | Checking | Done |
| BoFA | Savings | Partial |
| BoFA | Credit | Partial |
| Amex | Checking | Needed |
| Amex | Credit | Partial |
| Chase | Checking | Done |
| Chase | Savings | Partial |
| Chase | Credit | Partial |
| Citi | Credit | Done |
| Marcus | Savings | Partial |
| Robinhood | Checking/Savings | Done (PDF + CSV, balance reconciliation) |
| Robinhood | Credit | Done (PDF) |
| Robinhood | Investment | Done (CSV) |
| Guideline | Investment | Done (CSV) |

**Parser** → `backend/apps/financial_account/institutions/parsers/` and `backend/apps/financial_account/services/statement_import_service.py`

Statements arrive via in-app upload or by dropping files into the account's Google Drive folder for the storage scanner to import.
