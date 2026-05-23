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

3. Start the agent in headless-only mode (works on every platform). The
   base `automation` service polls for tasks and runs `scheduled_download`
   / `manual_download` runs without a display:

   ```bash
   docker compose up -d --build automation
   docker compose logs -f automation
   ```

4. Enable headed Chromium so `interactive_login` tasks can pop a real
   browser window. **Docker Desktop on Linux cannot mount
   `/tmp/.X11-unix`** without manual file-sharing setup, so we use a
   TCP bridge on the host instead:

   ```bash
   ./scripts/bank_sync/start-headed.sh
   ```

   Or step by step:

   ```bash
   xhost +local:
   cp "$XAUTHORITY" local_data/.xauthority
   python3 scripts/bank_sync/x11_bridge.py   # leave running
   docker compose -f docker-compose.yml -f docker-compose.x11.yml up -d automation
   ```

   Platform notes:

   - **Linux + Docker Desktop** (recommended path above): the bridge
     listens on `0.0.0.0:6000` and the container uses
     `DISPLAY=host.docker.internal:0` with the copied X authority cookie.
   - **Linux + native Docker**: you can mount the unix socket directly by
     setting `BANK_SYNC_X11_DISPLAY=:0` and bind-mounting
     `/tmp/.X11-unix:/tmp/.X11-unix:rw` in a local override, or use the
     same TCP bridge script.
   - **macOS / Windows**: install XQuartz (macOS) or VcXsrv (Windows),
     allow network clients, and set `BANK_SYNC_X11_DISPLAY=host.docker.internal:0`
     in `.env`.

## Adding a new bank

Add a `BaseInstitutionAdapter` subclass under
`scripts/bank_sync/institutions/`, then register the class in
`scripts/bank_sync/institutions/__init__.py`. Adapters never see
credentials; they only navigate, capture cookies, and download CSV/XLS
files.

The agent dispatches by the `institution_slug` value the API sends per
task. Aliases (e.g. `bofa` ↔ `bank_of_america`) live in the
`_REGISTRY` dict at the top of `institutions/__init__.py`.
