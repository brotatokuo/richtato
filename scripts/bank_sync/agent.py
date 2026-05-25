"""``bank-agent`` host CLI: independent of the Richtato app.

The agent keeps its own Fernet-encrypted SQLite vault under
``local_data/bank-agent/agent.db`` for bank logins, per-account
activity URLs, and a poll schedule. It uploads downloaded statements
to each account's Google Drive folder through the Richtato backend.

Run ``python -m scripts.bank_sync.agent --help`` for the full command
surface. Common usage:

.. code-block:: bash

    # one-time setup
    export BANK_AGENT_FERNET_KEY="$(python -m scripts.bank_sync.agent generate-key)"

    bank-agent login add bofa --nickname personal --cadence daily --hour 6
    bank-agent login signin 1

    bank-agent account add 1 \\
        --activity-url "https://bofa.test/activity?adx=ABC" \\
        --storage-uri "gdrive://<account_folder_id>" \\
        --flow deposit

    bank-agent status
    bank-agent sync 1
    bank-agent run            # daemon loop
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Sequence
from urllib.parse import urljoin

from loguru import logger

from scripts.bank_sync import agent_store as store_mod
from scripts.bank_sync.agent_store import (
    AgentStore,
    Login,
    dumps as agent_dumps,
    export_to_dict,
    import_from_dict,
)
from scripts.bank_sync.encryption import MissingAgentKey, generate_key
from scripts.bank_sync.cli_hints import signin_command_hint
from scripts.bank_sync.errors import FailureKind, parse_failure_kind, strip_failure_prefix


def _lazy_worker():
    """Import the Playwright worker module on demand.

    Pulling Playwright in eagerly slows down (and can break) commands
    like ``status`` / ``account list`` on machines without it installed.
    """
    from scripts.bank_sync import worker

    return worker


def _configure_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=os.getenv("BANK_AGENT_LOG_LEVEL", "INFO"))


def _store(args: argparse.Namespace) -> AgentStore:
    """Build an AgentStore from CLI args (``--db`` override or default)."""
    db_path = getattr(args, "db", None)
    return AgentStore(db_path=db_path)


def _failure_action_message(
    kind: FailureKind | None,
    *,
    login_id: int | None = None,
) -> str | None:
    if kind is None:
        return None
    messages = {
        FailureKind.NEEDS_REAUTH: (
            f"Login needs re-auth; run {signin_command_hint(login_id)} to refresh cookies."
        ),
        FailureKind.DOM_BROKEN: (
            "Bank page layout changed; automation needs an adapter update."
        ),
        FailureKind.NO_DOWNLOAD: "No statement or balance was produced (session looks OK).",
        FailureKind.IMPORT_REJECTED: (
            "Download succeeded but Richtato rejected the upload."
        ),
        FailureKind.LOGIN_CANCELLED: (
            f"Sign-in was cancelled; run {signin_command_hint(login_id)} again."
        ),
        FailureKind.CONFIG: "Fix the bank-agent configuration and retry.",
        FailureKind.UNKNOWN: "Unexpected error; check logs for details.",
    }
    return messages.get(kind)


def _print_failure_details(outcome, *, login_id: int | None = None) -> None:
    kind = outcome.failure_kind or parse_failure_kind(outcome.failure_reason)
    if outcome.account_failures:
        if len(outcome.account_failures) == 1:
            failure = outcome.account_failures[0]
            print(
                f"Failure [{failure.kind}]: Account {failure.account_id}: {failure.message}",
                file=sys.stderr,
            )
        else:
            primary_kind = kind or outcome.account_failures[0].kind
            print(f"Failure [{primary_kind}]:", file=sys.stderr)
            for failure in outcome.account_failures:
                print(
                    f"  Account {failure.account_id}: {failure.message}",
                    file=sys.stderr,
                )
    elif outcome.failure_reason:
        label = f" [{kind}]" if kind else ""
        detail = strip_failure_prefix(outcome.failure_reason)
        print(f"Failure{label}: {detail}", file=sys.stderr)

    action = _failure_action_message(kind, login_id=login_id)
    if action and not outcome.needs_reauth:
        print(f"Action: {action}", file=sys.stderr)
    elif outcome.needs_reauth:
        print(
            f"Action: Login needs re-auth; run {signin_command_hint(login_id)} to refresh cookies.",
            file=sys.stderr,
        )


def _print_login(login: Login, accounts_count: int) -> None:
    print(
        f"#{login.id} [{login.institution_slug}] {login.nickname or '(default)'}"
        f"  status={login.status} cadence={login.cadence}@{login.preferred_run_hour_local:02d}"
        f"  next_run={login.next_run_at or '-'}  last_success={login.last_success_at or '-'}"
        f"  accounts={accounts_count}"
    )
    if login.last_failure_reason:
        kind = parse_failure_kind(login.last_failure_reason)
        label = f" [{kind}]" if kind else ""
        detail = strip_failure_prefix(login.last_failure_reason)
        print(f"     last_failure{label}: {detail}")
        action = _failure_action_message(kind, login_id=login.id)
        if action:
            print(f"     action: {action}")


def _print_login_status(login: Login, accounts) -> None:
    label = login.nickname or "default"
    print(f"Login #{login.id}  {login.institution_slug} / {label}")
    print(
        f"  Status: {login.status} | "
        f"Cadence: {login.cadence} at {login.preferred_run_hour_local:02d}:00 | "
        f"Accounts: {len(accounts)}"
    )
    print(f"  Last success: {login.last_success_at or '-'}")
    print(f"  Next run: {login.next_run_at or '-'}")
    if login.last_failure_reason:
        kind = parse_failure_kind(login.last_failure_reason)
        label = f" [{kind}]" if kind else ""
        detail = strip_failure_prefix(login.last_failure_reason)
        print(f"  Last failure{label}: {detail}")
        action = _failure_action_message(kind, login_id=login.id)
        if action:
            print(f"  Action: {action}")

    if not accounts:
        print("  Accounts: none")
        return

    print("  Accounts:")
    for account in accounts:
        enabled = "on" if account.enabled else "off"
        name = account.detected_account_name or "(unset)"
        print(f"    #{account.id}  {name}")
        print(
            f"       Flow: {account.flow} | "
            f"Enabled: {enabled} | "
            f"Last success: {account.last_success_at or '-'}"
        )
        if account.richtato_account_id is not None:
            print(f"       Richtato account ID: {account.richtato_account_id}")
        print(f"       Storage URI: {account.storage_uri or '(none)'}")


# ============================= login commands ==========================


def cmd_login_add(args: argparse.Namespace) -> int:
    store = _store(args)
    try:
        login = store.add_login(
            institution_slug=args.institution,
            nickname=args.nickname,
            cadence=args.cadence,
            preferred_run_hour_local=args.hour,
        )
    except Exception as exc:
        print(f"Error adding login: {exc}", file=sys.stderr)
        return 2
    print(
        f"Created login {login.id} ({login.institution_slug}/{login.nickname or 'default'})."
    )
    print("Next step: bank-agent login signin", login.id)
    return 0


def cmd_login_list(args: argparse.Namespace) -> int:
    store = _store(args)
    logins = store.list_logins()
    if not logins:
        print("No logins configured yet. Use `bank-agent login add` to start.")
        return 0
    for login in logins:
        accounts = store.list_accounts(login.id)
        _print_login(login, len(accounts))
    return 0


def cmd_login_signin(args: argparse.Namespace) -> int:
    store = _store(args)
    worker = _lazy_worker()
    succeeded, message = asyncio.run(worker.interactive_login(store, args.login_id))
    print(message)
    return 0 if succeeded else 2


def cmd_login_remove(args: argparse.Namespace) -> int:
    store = _store(args)
    login = store.get_login(args.login_id)
    if login is None:
        print(f"Login {args.login_id} not found.", file=sys.stderr)
        return 1
    if not args.yes:
        print(
            f"Refusing to delete login {login.id} ({login.institution_slug}) without --yes.",
            file=sys.stderr,
        )
        return 1
    store.delete_login(args.login_id)
    print(f"Deleted login {args.login_id} and its accounts.")
    return 0


def cmd_login_schedule(args: argparse.Namespace) -> int:
    store = _store(args)
    if store.get_login(args.login_id) is None:
        print(f"Login {args.login_id} not found.", file=sys.stderr)
        return 1
    store.update_login_schedule(
        args.login_id,
        cadence=args.cadence,
        preferred_run_hour_local=args.hour,
    )
    print("Schedule updated.")
    return 0


# ============================ account commands =========================


def cmd_account_add(args: argparse.Namespace) -> int:
    store = _store(args)
    if store.get_login(args.login_id) is None:
        print(f"Login {args.login_id} not found.", file=sys.stderr)
        return 1
    try:
        account = store.add_account(
            login_id=args.login_id,
            storage_uri=args.storage_uri or "",
            activity_url=args.activity_url,
            flow=args.flow,
            detected_account_name=args.name,
            richtato_account_id=args.richtato_account_id,
        )
    except Exception as exc:
        print(f"Error adding account: {exc}", file=sys.stderr)
        return 2
    print(f"Created account {account.id} under login {account.login_id}.")
    if account.storage_uri:
        print(f"  storage_uri: {account.storage_uri}")
    if account.richtato_account_id is not None:
        print(f"  richtato_account_id: {account.richtato_account_id}")
    return 0


def cmd_account_list(args: argparse.Namespace) -> int:
    store = _store(args)
    accounts = store.list_accounts(args.login_id)
    if not accounts:
        print("No accounts configured.")
        return 0
    for account in accounts:
        enabled = "on" if account.enabled else "off"
        print(
            f"#{account.id} login={account.login_id} flow={account.flow} enabled={enabled} "
            f"last_success={account.last_success_at or '-'}"
        )
        print(f"     name: {account.detected_account_name or '(unset)'}")
        print(f"     storage_uri: {account.storage_uri or '(none)'}")
        if account.richtato_account_id is not None:
            print(f"     richtato_account_id: {account.richtato_account_id}")
    return 0


def cmd_account_update(args: argparse.Namespace) -> int:
    store = _store(args)
    if store.get_account(args.account_id) is None:
        print(f"Account {args.account_id} not found.", file=sys.stderr)
        return 1
    store.update_account(
        args.account_id,
        activity_url=args.activity_url,
        flow=args.flow,
        storage_uri=args.storage_uri,
        detected_account_name=args.name,
        richtato_account_id=args.richtato_account_id,
        enabled=args.enabled,
    )
    print(f"Updated account {args.account_id}.")
    return 0


def cmd_account_remove(args: argparse.Namespace) -> int:
    store = _store(args)
    if store.get_account(args.account_id) is None:
        print(f"Account {args.account_id} not found.", file=sys.stderr)
        return 1
    store.delete_account(args.account_id)
    print(f"Deleted account {args.account_id}.")
    return 0


# ============================ sync commands ============================


def cmd_sync(args: argparse.Namespace) -> int:
    store = _store(args)
    worker = _lazy_worker()
    outcome = asyncio.run(
        worker.download_login(
            store,
            args.login_id,
            kind="manual_download",
            headed=args.headed,
        )
    )
    print(
        f"Attempted={outcome.attempted} succeeded={outcome.succeeded} "
        f"files={outcome.files_downloaded} status={outcome.run_status}"
    )
    if outcome.failure_reason or outcome.account_failures:
        _print_failure_details(outcome, login_id=args.login_id)
        from scripts.bank_sync.notification_client import post_failure_event

        post_failure_event(
            store=store,
            login_id=args.login_id,
            outcome=outcome,
            event_type="manual_download",
        )
    if outcome.needs_reauth:
        return 2
    return 0 if outcome.run_status == "completed" else 2


def cmd_status(args: argparse.Namespace) -> int:
    store = _store(args)
    logins = store.list_logins()
    if not logins:
        print("No logins configured.")
        return 0
    for index, login in enumerate(logins):
        accounts = store.list_accounts(login.id)
        if index:
            print()
        _print_login_status(login, accounts)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    store = _store(args)
    worker = _lazy_worker()
    poll_seconds = args.poll_seconds
    logger.info("bank-agent run loop online; polling every {}s", poll_seconds)

    stop = {"flag": False}

    def _shutdown(*_):
        logger.info("Shutdown signal received; stopping after current task.")
        stop["flag"] = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _shutdown)
        except ValueError:
            pass

    while not stop["flag"]:
        due = store.due_logins()
        for login in due:
            if stop["flag"]:
                break
            logger.info(
                "Running scheduled download for login {} ({})",
                login.id,
                login.institution_slug,
            )
            try:
                outcome = asyncio.run(
                    worker.download_login(store, login.id, kind="scheduled_download")
                )
                if outcome.failure_reason or outcome.account_failures:
                    from scripts.bank_sync.notification_client import post_failure_event

                    post_failure_event(
                        store=store,
                        login_id=login.id,
                        outcome=outcome,
                        event_type="scheduled_download",
                    )
            except Exception:
                logger.exception(
                    "Unhandled error during scheduled download for login {}", login.id
                )
        if stop["flag"]:
            break
        time.sleep(poll_seconds)

    logger.info("bank-agent run loop stopped.")
    return 0


# ============================ key + import/export =====================


def cmd_apply(args: argparse.Namespace) -> int:
    """Upsert logins and accounts from a YAML config file into the vault.

    Cookies are never read or overwritten here. The setup YAML is authoritative
    for structural config and activity URLs — institution, nickname, cadence,
    hour, storage_uri, flow, name, and per-account activity_url. Run
    ``login signin`` afterward to capture cookies for any newly added logins.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        print(
            "PyYAML is not installed. Run: pip install PyYAML",
            file=sys.stderr,
        )
        return 3

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        raw = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        print(f"Failed to parse YAML: {exc}", file=sys.stderr)
        return 1

    if not isinstance(raw, dict) or "logins" not in raw:
        print("Config must have a top-level 'logins' list.", file=sys.stderr)
        return 1

    _apply_env_block(raw.get("env"))

    store = _store(args)
    return _apply_config_payload(raw, store)


def _apply_env_block(env_block) -> None:
    """Load host credentials from an optional setup YAML env block."""
    if not isinstance(env_block, dict):
        return
    for key in ("RICHTATO_API_TOKEN", "BANK_AGENT_FERNET_KEY"):
        value = env_block.get(key)
        if value:
            os.environ[key] = str(value)


def _apply_config_payload(raw: dict, store: AgentStore) -> int:
    """Upsert generated/YAML config into the local vault.

    This intentionally preserves stored cookies. The config owns login schedule,
    account name/flow/storage, and activity URLs when provided.
    """

    logins_added = logins_updated = accounts_added = accounts_updated = 0

    for login_cfg in raw.get("logins") or []:
        institution = login_cfg.get("institution", "").strip()
        if not institution:
            print("Skipping login entry with no 'institution'.", file=sys.stderr)
            continue

        nickname = str(login_cfg.get("nickname", "") or "")
        cadence = str(login_cfg.get("cadence", "daily"))
        hour = int(login_cfg.get("hour", 6))

        existing_login = next(
            (
                lo
                for lo in store.list_logins()
                if lo.institution_slug == institution and lo.nickname == nickname
            ),
            None,
        )

        if existing_login is None:
            login = store.add_login(
                institution_slug=institution,
                nickname=nickname,
                cadence=cadence,
                preferred_run_hour_local=hour,
            )
            logins_added += 1
            print(
                f"  + login #{login.id} [{institution}]"
                + (f" ({nickname})" if nickname else "")
                + f"  cadence={cadence}@{hour:02d}"
            )
        else:
            login = existing_login
            schedule_changed = (
                login.cadence != cadence or login.preferred_run_hour_local != hour
            )
            if schedule_changed:
                store.update_login_schedule(
                    login.id, cadence=cadence, preferred_run_hour_local=hour
                )
                logins_updated += 1
                print(
                    f"  ~ login #{login.id} [{institution}]"
                    + (f" ({nickname})" if nickname else "")
                    + f"  cadence={cadence}@{hour:02d} (updated)"
                )
            else:
                print(
                    f"  = login #{login.id} [{institution}]"
                    + (f" ({nickname})" if nickname else "")
                    + "  (unchanged)"
                )

        existing_accounts_by_uri = {
            acc.storage_uri: acc
            for acc in store.list_accounts(login.id)
            if acc.storage_uri
        }
        existing_accounts_by_richtato_id = {
            acc.richtato_account_id: acc
            for acc in store.list_accounts(login.id)
            if acc.richtato_account_id is not None
        }

        for acc_cfg in login_cfg.get("accounts") or []:
            storage_uri = str(acc_cfg.get("storage_uri", "") or "").strip()
            name = str(acc_cfg.get("name", "") or "")
            flow = str(acc_cfg.get("flow", "deposit"))
            activity_url = (
                str(acc_cfg.get("activity_url", "") or "").strip()
                if "activity_url" in acc_cfg
                else None
            )
            richtato_account_id = acc_cfg.get("richtato_account_id")
            if richtato_account_id is not None:
                richtato_account_id = int(richtato_account_id)

            if not storage_uri and flow != "investment_balance":
                print(
                    "  Skipping account entry with no 'storage_uri'.", file=sys.stderr
                )
                continue
            if flow == "investment_balance" and not richtato_account_id:
                print(
                    "  Skipping investment_balance account with no 'richtato_account_id'.",
                    file=sys.stderr,
                )
                continue

            existing = None
            if storage_uri and storage_uri in existing_accounts_by_uri:
                existing = existing_accounts_by_uri[storage_uri]
            elif (
                richtato_account_id
                and richtato_account_id in existing_accounts_by_richtato_id
            ):
                existing = existing_accounts_by_richtato_id[richtato_account_id]

            if existing is None:
                account = store.add_account(
                    login_id=login.id,
                    storage_uri=storage_uri,
                    activity_url=activity_url or "",
                    flow=flow,
                    detected_account_name=name,
                    richtato_account_id=richtato_account_id,
                )
                accounts_added += 1
                print(f"    + account #{account.id} {name!r} flow={flow}")
                if storage_uri:
                    print(f"      storage_uri: {storage_uri}")
                if richtato_account_id:
                    print(f"      richtato_account_id: {richtato_account_id}")
                if activity_url:
                    print("      activity_url: configured")
            else:
                account = existing
                changed = (
                    account.detected_account_name != name
                    or account.flow != flow
                    or account.richtato_account_id != richtato_account_id
                    or (
                        activity_url is not None
                        and account.activity_url != activity_url
                    )
                )
                if changed:
                    update_kwargs = {
                        "detected_account_name": name,
                        "flow": flow,
                        "richtato_account_id": richtato_account_id,
                    }
                    if activity_url is not None:
                        update_kwargs["activity_url"] = activity_url
                    store.update_account(account.id, **update_kwargs)
                    accounts_updated += 1
                    print(f"    ~ account #{account.id} {name!r} flow={flow} (updated)")
                else:
                    print(f"    = account #{account.id} {name!r} (unchanged)")

    print(
        f"\nDone: {logins_added} login(s) added, {logins_updated} updated, "
        f"{accounts_added} account(s) added, {accounts_updated} updated."
    )
    pending = [lo for lo in store.list_logins() if lo.status == "pending_login"]
    if pending:
        print("\nLogins awaiting sign-in:")
        for lo in pending:
            label = f"[{lo.institution_slug}]" + (
                f" ({lo.nickname})" if lo.nickname else ""
            )
            print(f"  bank-agent login signin {lo.id}   # {label}")
    return 0


def cmd_sync_config(args: argparse.Namespace) -> int:
    """Fetch generated config from Richtato and upsert it into the local vault."""

    try:
        import requests
    except ModuleNotFoundError:
        print("requests is not installed. Run: pip install requests", file=sys.stderr)
        return 3

    token = args.token or os.environ.get("RICHTATO_API_TOKEN", "")
    if not token:
        print(
            "Missing API token. Pass --token or set RICHTATO_API_TOKEN.",
            file=sys.stderr,
        )
        return 2

    base_url = (
        args.api_base
        or os.environ.get("RICHTATO_API_BASE_URL")
        or "http://127.0.0.1:8000/api/v1"
    ).rstrip("/")
    endpoint = urljoin(base_url + "/", "accounts/bank-agent-config/")
    params = {
        "nickname": args.nickname,
    }
    if args.all_supported:
        params["include"] = "all-supported"

    try:
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Token {token}"},
            params=params,
            timeout=20,
        )
    except requests.RequestException as exc:
        print(f"Failed to fetch Richtato config: {exc}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        print(
            f"Richtato config fetch failed: HTTP {response.status_code} {response.text[:500]}",
            file=sys.stderr,
        )
        return 1

    try:
        raw = response.json()
    except ValueError as exc:
        print(f"Richtato returned invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(raw, dict) or "logins" not in raw:
        print(
            "Richtato config response must have a top-level 'logins' list.",
            file=sys.stderr,
        )
        return 1

    return _apply_config_payload(raw, _store(args))


def cmd_generate_key(args: argparse.Namespace) -> int:
    print(generate_key())
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    store = _store(args)
    payload = export_to_dict(store)
    text = agent_dumps(payload)
    if args.output:
        Path(args.output).write_text(text)
        print(f"Wrote export to {args.output}")
    else:
        print(text)
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    store = _store(args)
    path = Path(args.input)
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        return 1
    payload = json.loads(path.read_text())
    logins, accounts = import_from_dict(store, payload)
    print(f"Imported {logins} login(s) and {accounts} account(s).")
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    """Serve the local-only HTTP API used by the Richtato setup UI."""

    from scripts.bank_sync.local_api import serve_local_api

    token = args.token or os.environ.get("BANK_AGENT_LOCAL_TOKEN", "")
    if not token:
        print(
            "Warning: BANK_AGENT_LOCAL_TOKEN is not set; local API requests are unauthenticated.",
            file=sys.stderr,
        )
    serve_local_api(store=_store(args), host=args.host, port=args.port, token=token)
    return 0


# ============================ parser ===================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bank-agent",
        description="Standalone bank-data polling agent for Richtato.",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"SQLite path (default: {store_mod.DEFAULT_DB_PATH}).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- login subcommands ----------------------------------------------
    p_login = sub.add_parser("login", help="Manage bank logins")
    login_sub = p_login.add_subparsers(dest="action", required=True)

    p_login_add = login_sub.add_parser("add", help="Create a new bank login")
    p_login_add.add_argument("institution", help="Institution slug (e.g. bofa, chase).")
    p_login_add.add_argument(
        "--nickname", default="", help="Optional nickname (e.g. 'Personal')."
    )
    p_login_add.add_argument("--cadence", default="daily", choices=store_mod.CADENCES)
    p_login_add.add_argument(
        "--hour", type=int, default=6, help="Preferred local run hour 0-23."
    )
    p_login_add.set_defaults(func=cmd_login_add)

    p_login_list = login_sub.add_parser("list", help="List configured logins")
    p_login_list.set_defaults(func=cmd_login_list)

    p_login_signin = login_sub.add_parser(
        "signin", help="Open headed Chromium to sign in / re-auth"
    )
    p_login_signin.add_argument("login_id", type=int)
    p_login_signin.set_defaults(func=cmd_login_signin)

    p_login_remove = login_sub.add_parser(
        "remove", help="Delete a login and all its accounts"
    )
    p_login_remove.add_argument("login_id", type=int)
    p_login_remove.add_argument("--yes", action="store_true", help="Confirm deletion")
    p_login_remove.set_defaults(func=cmd_login_remove)

    p_login_schedule = login_sub.add_parser(
        "schedule", help="Update cadence and preferred hour"
    )
    p_login_schedule.add_argument("login_id", type=int)
    p_login_schedule.add_argument("--cadence", choices=store_mod.CADENCES)
    p_login_schedule.add_argument("--hour", type=int)
    p_login_schedule.set_defaults(func=cmd_login_schedule)

    # ---- account subcommands --------------------------------------------
    p_account = sub.add_parser("account", help="Manage per-bank-account bindings")
    account_sub = p_account.add_subparsers(dest="action", required=True)

    p_account_add = account_sub.add_parser("add", help="Add an account under a login")
    p_account_add.add_argument("login_id", type=int)
    p_account_add.add_argument(
        "--storage-uri",
        default="",
        help="Google Drive folder URI (gdrive://<folder_id>) from Richtato account config.",
    )
    p_account_add.add_argument(
        "--activity-url", default="", help="Bank-side download URL (encrypted at rest)."
    )
    p_account_add.add_argument(
        "--flow", default="deposit", choices=store_mod.ACCOUNT_FLOWS
    )
    p_account_add.add_argument(
        "--name", default="", help="Detected/account display name."
    )
    p_account_add.add_argument(
        "--richtato-account-id",
        type=int,
        default=None,
        help="Richtato FinancialAccount id (required for investment_balance flow).",
    )
    p_account_add.set_defaults(func=cmd_account_add)

    p_account_list = account_sub.add_parser("list", help="List bank-side accounts")
    p_account_list.add_argument("--login-id", type=int, default=None)
    p_account_list.set_defaults(func=cmd_account_list)

    p_account_update = account_sub.add_parser("update", help="Update an account")
    p_account_update.add_argument("account_id", type=int)
    p_account_update.add_argument("--storage-uri")
    p_account_update.add_argument("--activity-url")
    p_account_update.add_argument("--flow", choices=store_mod.ACCOUNT_FLOWS)
    p_account_update.add_argument("--name")
    p_account_update.add_argument("--richtato-account-id", type=int, default=None)
    enabled_group = p_account_update.add_mutually_exclusive_group()
    enabled_group.add_argument(
        "--enable",
        dest="enabled",
        action="store_const",
        const=True,
        default=None,
    )
    enabled_group.add_argument(
        "--disable",
        dest="enabled",
        action="store_const",
        const=False,
    )
    p_account_update.set_defaults(func=cmd_account_update)

    p_account_remove = account_sub.add_parser(
        "remove", help="Delete an account binding"
    )
    p_account_remove.add_argument("account_id", type=int)
    p_account_remove.set_defaults(func=cmd_account_remove)

    # ---- top-level commands ---------------------------------------------
    p_sync = sub.add_parser("sync", help="Run one manual download for a login")
    p_sync.add_argument("login_id", type=int)
    p_sync.add_argument(
        "--headed",
        action="store_true",
        help="Run the manual sync in visible Chromium for debugging bank pages.",
    )
    p_sync.set_defaults(func=cmd_sync)

    p_status = sub.add_parser(
        "status", help="Show all logins, accounts, and schedule state"
    )
    p_status.set_defaults(func=cmd_status)

    p_run = sub.add_parser("run", help="Daemon loop: poll due logins and download")
    p_run.add_argument(
        "--poll-seconds",
        type=int,
        default=int(os.environ.get("BANK_AGENT_POLL_SECONDS", "60")),
        help="Seconds between schedule checks (default 60).",
    )
    p_run.set_defaults(func=cmd_run)

    p_apply = sub.add_parser(
        "apply",
        help="Upsert logins and accounts from a YAML config file",
    )
    p_apply.add_argument(
        "config",
        nargs="?",
        default="scripts/bank_sync/bank_sync.yml",
        help="Path to YAML config (default: scripts/bank_sync/bank_sync.yml).",
    )
    p_apply.set_defaults(func=cmd_apply)

    p_sync_config = sub.add_parser(
        "sync-config",
        help="Fetch generated config from Richtato and upsert it into the local vault",
    )
    p_sync_config.add_argument(
        "--api-base",
        default=None,
        help="Richtato API base URL (default: RICHTATO_API_BASE_URL or http://127.0.0.1:8000/api/v1).",
    )
    p_sync_config.add_argument(
        "--token", default=None, help="DRF token (default: RICHTATO_API_TOKEN)."
    )
    p_sync_config.add_argument("--cadence", default="daily", choices=store_mod.CADENCES)
    p_sync_config.add_argument(
        "--hour", type=int, default=6, help="Preferred local run hour (0-23)."
    )
    p_sync_config.add_argument("--nickname", default="personal")
    p_sync_config.add_argument(
        "--all-supported",
        action="store_true",
        help="Include all active supported accounts, not just sync_mode=auto.",
    )
    p_sync_config.set_defaults(func=cmd_sync_config)

    p_genkey = sub.add_parser(
        "generate-key", help="Print a fresh BANK_AGENT_FERNET_KEY value"
    )
    p_genkey.set_defaults(func=cmd_generate_key)

    p_export = sub.add_parser(
        "export", help="Dump the agent vault to JSON (encrypted blobs included)"
    )
    p_export.add_argument("--output", type=str, default=None)
    p_export.set_defaults(func=cmd_export)

    p_import = sub.add_parser(
        "import", help="Restore the agent vault from a JSON export"
    )
    p_import.add_argument(
        "input", type=str, help="Path to a previously exported JSON file"
    )
    p_import.set_defaults(func=cmd_import)

    p_api = sub.add_parser(
        "api",
        help="Serve a loopback HTTP API for setup/status/actions",
    )
    p_api.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host. Keep this on 127.0.0.1 unless you fully trust the network.",
    )
    p_api.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("BANK_AGENT_API_PORT", "8765")),
    )
    p_api.add_argument(
        "--token",
        default=None,
        help="Bearer token required by the local API (default: BANK_AGENT_LOCAL_TOKEN).",
    )
    p_api.set_defaults(func=cmd_api)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MissingAgentKey as exc:
        print(str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
