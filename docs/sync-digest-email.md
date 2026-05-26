# Daily bank-sync digest email (Resend)

Richtato can email a daily summary of host bank-agent sync health and recent statement imports. Delivery uses [Resend](https://resend.com/) on the free tier (3,000 emails/month, 100/day).

## Resend setup

1. Create a Resend account and add an API key.
2. Verify a sending domain (e.g. `notifications.yourdomain.com`).
3. Add to `.env`:

```bash
RESEND_API_KEY=re_xxxxxxxx
RESEND_FROM_EMAIL=Richtato <sync@notifications.yourdomain.com>
```

Until the domain is verified, Resend may only deliver to your own address for testing.

Optional: override the bank-agent database path (default is repo `local_data/bank-agent/agent.db`, or `/local_data/bank-agent/agent.db` inside Docker):

```bash
BANK_AGENT_DB_PATH=/local_data/bank-agent/agent.db
```

## Who receives email

- Active users with a non-empty `email`
- `UserPreference.notifications_enabled` is true (toggle in **Preferences → Notifications**)
- `UserPreference.bank_sync_daily_digest` is true

Immediate failure emails are separate and opt-in through **Preferences → Notifications → Bank Sync Alerts**. In-app bank-sync alerts are the default minimum notification path.

## Manual send / preview

From the backend container or `backend/` directory:

```bash
# Preview without sending
python manage.py send_sync_digest --dry-run

# One user
python manage.py send_sync_digest --user-id 1 --dry-run
python manage.py send_sync_digest --user-id 1

# Custom lookback window (default 24 hours)
python manage.py send_sync_digest --since-hours 48
```

Docker:

```bash
docker compose exec backend python manage.py send_sync_digest --dry-run
```

## Daily schedule (host cron)

Bank sync runs on the host; schedule the digest with host `crontab` (not a Docker sidecar):

```bash
0 7 * * * cd /home/alan/richtato && docker compose exec -T backend python manage.py send_sync_digest
```

Adjust the hour to after your typical sync window.

## Email contents

- **Bank agent** (`local_data/bank-agent/agent.db`): login status, cadence, last success/failure, linked accounts, recent runs (filtered to accounts you own)
- **Statement imports**: `StatementFile` rows with `source=agent_drop` in the lookback window
- **Setup gaps**: auto-sync accounts missing Drive storage or activity URL (same rules as Setup → Sync)

Subject line: `Richtato bank sync — All OK` or `Richtato bank sync — Needs attention`.

## Architecture note

The agent vault is **per machine**, not per Django user. On a shared household host, each notified user sees agent data only for logins linked to their `FinancialAccount` rows via `richtato_account_id`.
