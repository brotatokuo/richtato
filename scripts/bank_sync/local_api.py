"""Local-only HTTP API for the host bank-agent.

The API is intentionally small and loopback-bound by the CLI. It exposes
status and operator actions to the Richtato frontend without returning
encrypted cookie state or bank activity URLs.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from loguru import logger

from scripts.bank_sync.agent_store import AgentStore
from scripts.bank_sync.errors import parse_failure_kind, strip_failure_prefix


def build_status_payload(store: AgentStore) -> dict[str, Any]:
    """Return a redacted summary of logins, accounts, and recent runs."""

    logins = store.list_logins()
    accounts_by_login: dict[int, list[dict[str, Any]]] = {}
    for account in store.list_accounts():
        accounts_by_login.setdefault(account.login_id, []).append(
            {
                "id": account.id,
                "login_id": account.login_id,
                "name": account.detected_account_name,
                "flow": account.flow,
                "storage_uri": account.storage_uri,
                "richtato_account_id": account.richtato_account_id,
                "enabled": account.enabled,
                "last_success_at": account.last_success_at,
                "has_activity_url": bool(account.activity_url_encrypted),
            }
        )

    login_rows = []
    reauth_required = False
    for login in logins:
        failure_kind = parse_failure_kind(login.last_failure_reason)
        if login.status == "needs_reauth" or failure_kind and failure_kind.value == "needs_reauth":
            reauth_required = True
        login_rows.append(
            {
                "id": login.id,
                "institution_slug": login.institution_slug,
                "nickname": login.nickname,
                "status": login.status,
                "cadence": login.cadence,
                "preferred_run_hour_local": login.preferred_run_hour_local,
                "next_run_at": login.next_run_at,
                "last_run_at": login.last_run_at,
                "last_success_at": login.last_success_at,
                "last_failure_kind": failure_kind.value if failure_kind else None,
                "last_failure_reason": strip_failure_prefix(login.last_failure_reason),
                "cookies_captured_at": login.cookies_captured_at,
                "accounts": accounts_by_login.get(login.id, []),
            }
        )

    return {
        "ok": True,
        "reauth_required": reauth_required,
        "login_count": len(logins),
        "account_count": sum(len(accounts) for accounts in accounts_by_login.values()),
        "logins": login_rows,
        "recent_runs": [
            {
                "id": run.id,
                "login_id": run.login_id,
                "kind": run.kind,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "files_downloaded": run.files_downloaded,
                "error_kind": parse_failure_kind(run.error).value if parse_failure_kind(run.error) else None,
                "error": strip_failure_prefix(run.error),
            }
            for run in store.list_runs(limit=25)
        ],
    }


class BankAgentApiServer(ThreadingHTTPServer):
    """Threading HTTP server carrying the agent store and auth token."""

    def __init__(
        self,
        server_address: tuple[str, int],
        store: AgentStore,
        *,
        token: str = "",
    ) -> None:
        super().__init__(server_address, BankAgentApiHandler)
        self.store = store
        self.token = token


class BankAgentApiHandler(BaseHTTPRequestHandler):
    server: BankAgentApiServer

    def log_message(self, fmt: str, *args: object) -> None:
        logger.info("bank-agent-api " + fmt, *args)

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        if not self._authorize():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"ok": True, "service": "richtato-bank-agent"})
            return
        if parsed.path == "/status":
            self._send_json(build_status_payload(self.server.store))
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_POST(self) -> None:
        if not self._authorize():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/apply":
            self._handle_apply()
            return
        if parsed.path.startswith("/logins/") and parsed.path.endswith("/signin"):
            self._handle_signin(parsed.path)
            return
        if parsed.path.startswith("/logins/") and parsed.path.endswith("/sync"):
            self._handle_sync(parsed.path, parse_qs(parsed.query))
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def _authorize(self) -> bool:
        token = self.server.token
        if not token:
            return True
        auth_header = self.headers.get("Authorization", "")
        local_token = self.headers.get("X-Bank-Agent-Token", "")
        expected = f"Bearer {token}"
        if auth_header == expected or local_token == token:
            return True
        self._send_error(HTTPStatus.UNAUTHORIZED, "Invalid bank-agent token")
        return False

    def _handle_apply(self) -> None:
        try:
            import yaml  # type: ignore[import-untyped]
        except ModuleNotFoundError:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "PyYAML is not installed")
            return

        body = self._read_json_body()
        yaml_text = str(body.get("yaml") or "")
        if not yaml_text:
            self._send_error(HTTPStatus.BAD_REQUEST, "Request body must include yaml")
            return
        try:
            raw = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, f"Failed to parse YAML: {exc}")
            return
        if not isinstance(raw, dict) or "logins" not in raw:
            self._send_error(HTTPStatus.BAD_REQUEST, "Config must have a top-level logins list")
            return

        from scripts.bank_sync.agent import _apply_config_payload, _apply_env_block

        _apply_env_block(raw.get("env"))
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = _apply_config_payload(raw, self.server.store)
        self._send_json(
            {
                "ok": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "status": build_status_payload(self.server.store),
            },
            status=HTTPStatus.OK if exit_code == 0 else HTTPStatus.BAD_REQUEST,
        )

    def _handle_signin(self, path: str) -> None:
        login_id = self._login_id_from_path(path)
        if login_id is None:
            return
        from scripts.bank_sync.agent import _lazy_worker

        worker = _lazy_worker()
        succeeded, message = asyncio.run(worker.interactive_login(self.server.store, login_id))
        self._send_json(
            {
                "ok": succeeded,
                "message": message,
                "status": build_status_payload(self.server.store),
            },
            status=HTTPStatus.OK if succeeded else HTTPStatus.BAD_REQUEST,
        )

    def _handle_sync(self, path: str, query: dict[str, list[str]]) -> None:
        login_id = self._login_id_from_path(path)
        if login_id is None:
            return
        headed = (query.get("headed") or ["0"])[0].lower() in {"1", "true", "yes"}
        from scripts.bank_sync.agent import _lazy_worker

        worker = _lazy_worker()
        outcome = asyncio.run(
            worker.download_login(
                self.server.store,
                login_id,
                kind="manual_download",
                headed=headed,
            )
        )
        if outcome.failure_reason or outcome.account_failures:
            from scripts.bank_sync.notification_client import post_failure_event

            post_failure_event(
                store=self.server.store,
                login_id=login_id,
                outcome=outcome,
                event_type="manual_download",
            )
        self._send_json(
            {
                "ok": outcome.run_status == "completed",
                "outcome": {
                    "attempted": outcome.attempted,
                    "succeeded": outcome.succeeded,
                    "files_downloaded": outcome.files_downloaded,
                    "run_status": outcome.run_status,
                    "needs_reauth": outcome.needs_reauth,
                    "failure_kind": outcome.failure_kind.value if outcome.failure_kind else None,
                    "failure_reason": strip_failure_prefix(outcome.failure_reason),
                },
                "status": build_status_payload(self.server.store),
            },
            status=HTTPStatus.OK if outcome.run_status in {"completed", "partial"} else HTTPStatus.BAD_REQUEST,
        )

    def _login_id_from_path(self, path: str) -> int | None:
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "logins":
            self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return None
        try:
            return int(parts[1])
        except ValueError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Invalid login id")
            return None

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}

    def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, default=str).encode("utf-8")
        origin = self.headers.get("Origin", "")
        allowed_origins = {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://richtato.com",
        }
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Bank-Agent-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"ok": False, "error": message}, status=status)


def serve_local_api(
    *,
    store: AgentStore,
    host: str,
    port: int,
    token: str = "",
) -> None:
    """Run the local API until interrupted."""

    server = BankAgentApiServer((host, port), store, token=token)
    logger.info("bank-agent local API listening on http://{}:{}", host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
