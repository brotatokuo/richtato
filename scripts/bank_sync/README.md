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
- `richtato bank` manages the local Playwright bank agent on your desktop. It
  handles setup, visible sign-in, headless statement downloads, daemon startup,
  and logs.

The bank agent talks to Django over `/api/v1/bank-sync/runner/*` with the
`RICHTATO_RUNNER_TOKEN` service account. It is not a Docker Compose service.

## Preferred setup

Download `richtato-bank-agent-setup.yml` from Richtato, leave it in the repo
root, then run:

```bash
richtato bank setup
```

The guided CLI creates or reuses `scripts/bank_sync/.venv`, installs the
agent requirements and Chromium, applies the setup YAML to the encrypted local
vault, shows configured logins, and lets you sign in or run an immediate sync.

Use `richtato bank` later for status, sign-in, manual sync, daemon startup, and
logs.

## Quick config from Richtato

Richtato can generate the structural agent config from active accounts whose
`sync_mode` is `auto`. The agent upserts that config into its local vault
without touching stored cookies or activity URLs:

```bash
python -m scripts.bank_sync.agent sync-config \
  --api-base http://127.0.0.1:8000/api/v1 \
  --token "$RICHTATO_API_TOKEN"
```

For debugging, export the same config as YAML from Django:

```bash
docker compose exec backend python manage.py export_bank_agent_config --user-id 1
```

Use `--all-supported` on either command to include all active supported bank
accounts instead of only `sync_mode=auto` accounts.

## Debug config with YAML

`scripts/bank_sync/bank_sync.yml` remains supported as a human-readable
debug/emergency format. Prefer generating it from Richtato so account IDs and
storage paths do not drift. Apply a YAML file with:

```bash
python -m scripts.bank_sync.agent apply
# or point at a different file:
python -m scripts.bank_sync.agent apply /path/to/my_config.yml
```

`apply` upserts logins and accounts into the encrypted SQLite vault. It never
touches cookies or activity URLs, so it is safe to re-run at any time. After
applying, sign in to any newly added logins:

```bash
python -m scripts.bank_sync.agent login signin <login_id>
```

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
   richtato bank daemon
   ```

   Run this after every reboot. The CLI creates `scripts/bank_sync/.venv` on
   first use (downloads Chromium once) and writes logs to
   `local_data/bank-agent.log`.

## Adding a new bank

Add a `BaseInstitutionAdapter` subclass under
`scripts/bank_sync/institutions/`, then register the class in
`scripts/bank_sync/institutions/__init__.py`. Adapters never see
credentials; they only navigate, capture cookies, and download CSV/XLS
files.

The agent dispatches by the `institution_slug` value the API sends per
task. Aliases (e.g. `bofa` ↔ `bank_of_america`) live in the
`_REGISTRY` dict at the top of `institutions/__init__.py`.
