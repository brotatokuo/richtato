# Statement download automation

This package automates the daily Playwright-driven download of bank statements
and posts them to the Richtato import API. It is designed to run as a
long-lived Docker service on a Linux desktop, with one interactive bootstrap
step per institution performed natively on the same desktop.

The flow has two halves:

1. **Bootstrap (native, interactive, one time per institution).** You log into
   each bank once in a real Chromium window and the existing
   `scripts/statement_downloader.py` saves the session cookies to
   `local_data/automation/storage_states/<institution>.json`.
2. **Daily runs (Docker, headless, unattended).** The `automation` service
   loads each saved session, downloads the latest activity, posts it to
   `http://backend:8000/api/v1/accounts/import-statement/`, and emails Gmail
   SMTP alerts on any failure.

No bank passwords are stored anywhere. The only secrets per institution are
session cookies, which expire every 30-90 days and trigger a re-bootstrap.

## Prerequisites

- The Linux desktop that runs the Docker stack also runs Chromium and has a
  display attached (the bootstrap step needs a visible browser for MFA).
- Python 3.10+ available natively on the desktop for the bootstrap venv.
- A Gmail account with 2FA enabled and an App Password generated for SMTP.
- Each supported account already exists inside Richtato (you'll need its
  numeric account ID).

## One-time setup

### 1. Create the bootstrap venv on the Linux desktop

```bash
cd /path/to/richtato
python -m venv .venv-bootstrap
source .venv-bootstrap/bin/activate
pip install playwright
playwright install chromium
```

The venv is only used by the host-side `scripts/statement_downloader.py` for
the interactive bootstrap. Daily runs happen entirely inside the
`automation` container and don't touch this venv.

### 2. Populate `.env`

Copy the keys from [`.env.example`](.env.example) into the project root
`.env` (which docker-compose already loads for the other services). The
critical ones:

- `RICHTATO_USER` / `RICHTATO_PASS` - a Django user the API will accept via
  HTTP Basic auth (typically your superuser).
- `GMAIL_USER` / `GMAIL_APP_PASSWORD` / `ALERT_TO` - omit to disable email
  alerts; failures will still be logged to `local_data/automation/logs/`.
- `AUTOMATION_ACCOUNT_IDS` - JSON object mapping institution slug to the
  Richtato account ID that should receive imports for that bank. Example:

  ```env
  AUTOMATION_ACCOUNT_IDS={"chase": 3, "fidelity": 5, "marcus": 2}
  ```

  Only institutions listed here can be imported. Omitted institutions will
  fail with a clear "no account ID configured" alert.
- `TZ` / `RUN_TIME` - controls when the daily job fires inside the container.

### 3. Start the stack

```bash
docker compose up -d --build automation
docker compose logs -f automation
```

The scheduler will log the next scheduled run time and then idle until that
time arrives.

## Bootstrap an institution

Run this on the Linux desktop (with the venv activated) once per institution:

```bash
source .venv-bootstrap/bin/activate
python scripts/statement_downloader.py chase \
  --storage-state local_data/automation/storage_states/chase.json
```

A Chromium window opens. Log in, complete MFA, navigate to the statements
page, and trigger any CSV/XLS download to confirm the session works. The
script captures cookies + localStorage and writes them to the JSON path.

The `automation` container reads the same folder via the docker-compose
volume mount, so no transfer step is needed. The next scheduled run (or an
immediate `--only` run) will pick up the new session.

Repeat for each of: `bofa`, `marcus`, `amex`, `robinhood_bank`, `fidelity`,
`robinhood_investments`, `guideline`, `chase`.

## Verify immediately

After bootstrapping, you can trigger an on-demand run without waiting for the
scheduler:

```bash
docker compose exec automation python -m scripts.automation.runner --only chase
```

Pass multiple `--only` flags to test a subset:

```bash
docker compose exec automation python -m scripts.automation.runner --only chase --only marcus
```

Omit `--only` for a full run.

## Alert email format

When anything fails, the notifier batches all failures (and any stale
institutions) into a single email at the end of the run. Each failure block
includes:

- Institution slug
- Error kind (`session_expired`, `dom_broken`, `no_download`, `import_rejected`,
  `config`, `unknown`)
- Reason and consecutive failure count
- Timestamp of the last successful run
- Exact bootstrap + verify commands to copy/paste

`stale` entries are added when an institution has not had a successful run in
`STALE_THRESHOLD_DAYS` (default 3) even if today's run produced no hard error
(e.g. the institution is disabled but the user expected a daily file).

## Re-auth workflow

1. Open the alert email - it lists the affected institutions.
2. On the Linux desktop, activate the bootstrap venv and re-run the
   `statement_downloader.py` command for each listed institution.
3. Optionally trigger an immediate verification via
   `docker compose exec automation python -m scripts.automation.runner --only <institution>`.

## Files & paths

| Path | Purpose |
|---|---|
| `scripts/automation/scheduler.py` | Container PID 1, fires the runner daily |
| `scripts/automation/runner.py` | One-shot orchestrator (also CLI entrypoint) |
| `scripts/automation/institutions/` | Per-bank navigation adapters |
| `scripts/automation/notifier.py` | Gmail SMTP alert helper |
| `scripts/automation/importer.py` | POSTs files to `/api/v1/accounts/import-statement/` |
| `local_data/automation/storage_states/<slug>.json` | Captured session per bank |
| `local_data/automation/state.json` | Last-run tracker (success/failure timestamps) |
| `local_data/automation/logs/` | loguru rotating logs |
| `local_data/statements/<slug>/` | Saved download files (same convention as manual upload) |

## Caveats

- Bank UIs change. Adapters in `scripts/automation/institutions/` are
  best-effort scaffolds and will need selector tweaks over time. The
  `dom_broken` alert tells you which one needs attention.
- Headless Chromium is detectable. The runner applies `playwright-stealth`
  if available, but Amex and other high-friction sites may still challenge.
  If a bank consistently fails headless, capture a session there manually
  every few days from the desktop browser as a fallback.
- The runner does **not** retry on failure. A single bad day for a bank
  produces one alert email - re-running is your call.
- TOTP/SMS MFA cannot be automated. Always handled during bootstrap.
