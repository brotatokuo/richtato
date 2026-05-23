"""``BankLogin`` and ``SyncedAccount`` lifecycle helpers."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.bank_sync.models import BankLogin, SyncedAccount
from apps.bank_sync.services.scheduling import reschedule
from apps.financial_account.models import FinancialAccount, FinancialInstitution


def create_login(
    *,
    user,
    institution: FinancialInstitution,
    nickname: str = "",
    cadence: str = "daily",
    preferred_run_hour_local: int = 6,
) -> BankLogin:
    """Create a ``BankLogin`` in ``pending_login`` state.

    Nickname defaults to the institution name when empty so the user always
    sees a recognisable label. ``unique_together(user, institution,
    nickname)`` means a duplicate name under the same institution returns
    the existing row instead of raising.
    """

    label = nickname.strip() or institution.name
    login, _ = BankLogin.objects.get_or_create(
        user=user,
        institution=institution,
        nickname=label,
        defaults={
            "status": "pending_login",
            "cadence": cadence,
            "preferred_run_hour_local": preferred_run_hour_local,
        },
    )
    return login


def update_login(login: BankLogin, **changes) -> BankLogin:
    """Apply partial updates and reschedule if cadence/hour changed."""

    cadence_changed = "cadence" in changes
    hour_changed = "preferred_run_hour_local" in changes
    for field in ("cadence", "preferred_run_hour_local", "nickname"):
        if field in changes:
            setattr(login, field, changes[field])
    if "enabled" in changes:
        login.status = "active" if changes["enabled"] else "disabled"
    login.save()
    if login.status == "active" and (cadence_changed or hour_changed):
        reschedule(login)
    elif login.status != "active":
        login.next_run_at = None
        login.save(update_fields=["next_run_at", "updated_at"])
    return login


def disable_login(login: BankLogin) -> BankLogin:
    """Pause automation without deleting stored cookies."""

    login.status = "disabled"
    login.next_run_at = None
    login.save(update_fields=["status", "next_run_at", "updated_at"])
    return login


def activate_after_capture(login: BankLogin) -> BankLogin:
    """Flip a login to ``active`` after the agent captured a fresh session.

    Resets failure counters and schedules the first cadence run so the user
    sees activity soon after connecting.
    """

    login.status = "active"
    login.consecutive_failures = 0
    login.last_failure_reason = ""
    login.save(
        update_fields=[
            "status",
            "consecutive_failures",
            "last_failure_reason",
            "updated_at",
        ]
    )
    reschedule(login)
    return login


def mark_needs_reauth(login: BankLogin, reason: str = "") -> BankLogin:
    """Flip a login to ``needs_reauth`` so the UI prompts a re-login."""

    login.status = "needs_reauth"
    login.last_failure_reason = reason or "Session cookies expired"
    login.next_run_at = None
    login.save(
        update_fields=[
            "status",
            "last_failure_reason",
            "next_run_at",
            "updated_at",
        ]
    )
    return login


@transaction.atomic
def bind_account(
    *,
    bank_login: BankLogin,
    financial_account: FinancialAccount,
    flow: str,
    external_account_token: str = "",
    activity_url: str = "",
    detected_account_name: str = "",
) -> SyncedAccount:
    """Bind a Richtato ``FinancialAccount`` to a ``BankLogin``.

    Idempotent on the ``financial_account`` OneToOne: re-binding overwrites
    the activity URL and token but keeps the existing row so run history
    via FK stays continuous. Also flips the account's ``sync_mode`` to
    ``auto`` so the UI badge and import paths reflect the new wiring.
    """

    synced, _ = SyncedAccount.objects.get_or_create(
        financial_account=financial_account,
        defaults={"bank_login": bank_login, "flow": flow},
    )
    # If the user moves an account between bank logins (rare), update the FK.
    if synced.bank_login_id != bank_login.id:
        synced.bank_login = bank_login
    synced.flow = flow or synced.flow or "deposit"
    if external_account_token:
        synced.external_account_token = external_account_token
    if detected_account_name:
        synced.detected_account_name = detected_account_name
    if activity_url:
        synced.activity_url = activity_url
    synced.enabled = True
    synced.save()

    if financial_account.sync_mode != "auto":
        financial_account.sync_mode = "auto"
        financial_account.save(update_fields=["sync_mode", "updated_at"])

    return synced


def unbind_account(synced: SyncedAccount) -> None:
    """Remove a SyncedAccount and reset the parent FinancialAccount's mode.

    Drops the binding row and flips ``sync_mode`` back to ``manual`` so the
    UI no longer advertises auto-sync for an account that has no agent
    coverage. Other sync modes (``upload``) are preserved when the user
    last imported a statement that way.
    """

    account = synced.financial_account
    synced.delete()
    if account.sync_mode == "auto":
        account.sync_mode = "manual"
        account.save(update_fields=["sync_mode", "updated_at"])


def touch_last_success(login: BankLogin) -> None:
    """Record a successful sync and reschedule the next run."""

    now = timezone.now()
    login.last_success_at = now
    login.last_run_at = now
    login.consecutive_failures = 0
    login.last_failure_reason = ""
    if login.status != "disabled":
        login.status = "active"
    login.save(
        update_fields=[
            "last_success_at",
            "last_run_at",
            "consecutive_failures",
            "last_failure_reason",
            "status",
            "updated_at",
        ]
    )
    reschedule(login)
