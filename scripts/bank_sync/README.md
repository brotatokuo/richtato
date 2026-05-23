# Bank-sync Playwright agent

Cookie-only, no passwords. The agent polls
`/api/v1/bank-sync/runner/due-tasks/` on a schedule and dispatches each
leased task:

- `interactive_login` — pops a headed Chromium window so the user signs in
  to their bank directly. Only the resulting Playwright `storage_state`
  (cookies + localStorage) is captured and posted back, encrypted with the
  user's per-tenant key.
- `scheduled_download` / `manual_download` — reuses the stored
  `storage_state` headless to download per-account statements and posts
  them to `/api/v1/accounts/import-statement/`.

## Runtime Shape

Richtato's full stack and the bank automation runtime are separate:

- `docker compose up -d` runs the app: Postgres, Django, and Vite.
- `./scripts/bank_sync/start-headed.sh` runs the local Playwright bank agent
  on your desktop. It handles both visible sign-in and headless statement
  downloads.

The bank agent talks to Django over `/api/v1/bank-sync/runner/*` with the
`RICHTATO_RUNNER_TOKEN` service account. It is not a Docker Compose service.

## Setup

1. Provision the agent's service account token:

   ```bash
   docker compose exec backend python manage.py create_automation_runner
   ```

   Copy the printed `RICHTATO_RUNNER_TOKEN=...` line into your `.env`.

2. Generate (or copy in) a Fernet master key:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Set it as `BANK_SYNC_FERNET_KEY` in `.env`. Required in production; dev
   falls back to a `SECRET_KEY`-derived key.

3. Start the Richtato app stack:

   ```bash
   docker compose up -d
   ```

4. Start the local bank agent before using **Connect bank → Open browser to
   sign in** or scheduled statement downloads:

   ```bash
   ./scripts/bank_sync/start-headed.sh
   ```

   Run this after every reboot. It creates `scripts/bank_sync/.venv` on
   first use (downloads Chromium once) and writes logs to
   `local_data/bank-sync-agent.log`.

## Adding a new bank

Add a `BaseInstitutionAdapter` subclass under
`scripts/bank_sync/institutions/`, then register the class in
`scripts/bank_sync/institutions/__init__.py`. Adapters never see
credentials; they only navigate, capture cookies, and download CSV/XLS
files.

The agent dispatches by the `institution_slug` value the API sends per
task. Aliases (e.g. `bofa` ↔ `bank_of_america`) live in the
`_REGISTRY` dict at the top of `institutions/__init__.py`.
