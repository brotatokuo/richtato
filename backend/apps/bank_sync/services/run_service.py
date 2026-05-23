"""``SyncRun`` queue + outcome handling.

The agent polls a single queue. Two task kinds use the same row shape so
the agent only needs one fetch endpoint:

* ``interactive_login``: spawn a headed browser, wait for the user to sign
  in, capture ``storage_state``, discover accounts.
* ``scheduled_download`` / ``manual_download``: reuse the stored
  ``storage_state`` headless to download per-account statements.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.bank_sync.models import BankLogin, SyncRun
from apps.bank_sync.services import login_service


def queue_interactive_login(login: BankLogin, *, triggered_by: str = "user_login") -> SyncRun:
    """Enqueue a headed login task. Cancels any earlier pending interactive run."""

    with transaction.atomic():
        SyncRun.objects.filter(
            bank_login=login,
            task_kind="interactive_login",
            status="queued",
        ).update(status="failed", failure_kind="login_cancelled", finished_at=timezone.now())
        return SyncRun.objects.create(
            bank_login=login,
            task_kind="interactive_login",
            triggered_by=triggered_by,
        )


def queue_manual_download(login: BankLogin) -> SyncRun:
    """Enqueue an immediate manual-download task and nudge ``next_run_at``."""

    run = SyncRun.objects.create(
        bank_login=login,
        task_kind="manual_download",
        triggered_by="manual",
    )
    login.next_run_at = timezone.now()
    login.save(update_fields=["next_run_at", "updated_at"])
    return run


def lease_due_tasks(
    *,
    limit: int = 25,
    task_kinds: tuple[str, ...] | None = None,
) -> list[SyncRun]:
    """Return queued tasks that are due, atomically marking them ``running``.

    Two kinds of "due":

    * ``interactive_login``: always immediately runnable.
    * ``scheduled_download`` / ``manual_download``: due when the parent
      ``BankLogin`` has ``status=active`` and ``next_run_at`` is past.

    ``task_kinds`` optionally restricts which queued rows this caller may
    lease. The Docker download agent passes download kinds only; the host
    interactive runner passes ``interactive_login`` so headed sign-in runs
    on the user's desktop instead of inside Docker Desktop.
    """

    download_kinds = ("scheduled_download", "manual_download")
    lease_downloads = task_kinds is None or any(k in task_kinds for k in download_kinds)

    now = timezone.now()
    leased: list[SyncRun] = []
    with transaction.atomic():
        if lease_downloads:
            # Promote due logins into scheduled_download rows if not already queued.
            due_logins = BankLogin.objects.select_for_update(skip_locked=True).filter(
                status="active",
                next_run_at__lte=now,
            )
            for login in due_logins:
                has_queued = SyncRun.objects.filter(
                    bank_login=login,
                    task_kind__in=download_kinds,
                    status="queued",
                ).exists()
                if not has_queued:
                    SyncRun.objects.create(
                        bank_login=login,
                        task_kind="scheduled_download",
                        triggered_by="scheduler",
                    )

        queued_qs = (
            SyncRun.objects.select_for_update(skip_locked=True)
            .filter(status="queued")
            .select_related("bank_login__institution")
            .order_by("queued_at")
        )
        if task_kinds is not None:
            queued_qs = queued_qs.filter(task_kind__in=task_kinds)
        for run in queued_qs[:limit]:
            run.status = "running"
            run.leased_at = now
            run.save(update_fields=["status", "leased_at"])
            leased.append(run)
    return leased


def record_outcome(
    run: SyncRun,
    *,
    succeeded: bool,
    failure_kind: str = "",
    failure_reason: str = "",
    accounts_attempted: int = 0,
    accounts_succeeded: int = 0,
    statements_imported: int = 0,
) -> SyncRun:
    """Finish a ``SyncRun`` and update the parent ``BankLogin`` state."""

    now = timezone.now()
    run.finished_at = now
    run.accounts_attempted = int(accounts_attempted)
    run.accounts_succeeded = int(accounts_succeeded)
    run.statements_imported = int(statements_imported)
    if succeeded:
        if accounts_succeeded and accounts_attempted and accounts_succeeded < accounts_attempted:
            run.status = "partial"
        else:
            run.status = "completed"
        run.failure_kind = ""
        run.failure_reason = ""
    else:
        run.status = "failed"
        run.failure_kind = failure_kind or "unknown"
        run.failure_reason = failure_reason
    run.save()

    login = run.bank_login
    login.last_run_at = now
    if succeeded:
        if run.task_kind in ("scheduled_download", "manual_download"):
            login_service.touch_last_success(login)
        else:
            # interactive_login success is finalised by RunnerCapturedSessionAPIView
            # via login_service.activate_after_capture, but reschedule defensively
            # in case the capture endpoint did not fire.
            login.last_run_at = now
            login.save(update_fields=["last_run_at", "updated_at"])
    else:
        login.consecutive_failures = (login.consecutive_failures or 0) + 1
        login.last_failure_reason = failure_reason or failure_kind or "Sync failed"
        if failure_kind == "needs_reauth":
            login_service.mark_needs_reauth(login, reason=failure_reason)
        elif login.consecutive_failures >= 3:
            login.status = "error"
            login.save(
                update_fields=[
                    "status",
                    "consecutive_failures",
                    "last_failure_reason",
                    "last_run_at",
                    "updated_at",
                ]
            )
        else:
            login.save(
                update_fields=[
                    "consecutive_failures",
                    "last_failure_reason",
                    "last_run_at",
                    "updated_at",
                ]
            )
    return run
