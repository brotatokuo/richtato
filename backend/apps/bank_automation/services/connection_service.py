"""Service layer for ingesting captured sessions and managing connections.

The Chrome extension POSTs an ``ingest_session`` payload that bundles the
storage_state cookies, the per-account activity URLs, and detected account
names. This service is the single place that fans that payload out into
``BankConnection``, ``BankAccountLink``, and ``BankSession`` rows.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone
from loguru import logger

from apps.bank_automation.models import (
    BankAccountLink,
    BankAutomationRun,
    BankConnection,
    BankSession,
)
from apps.bank_automation.services.scheduling import reschedule
from apps.financial_account.models import FinancialAccount, FinancialInstitution


@dataclass(frozen=True)
class CapturedAccount:
    """One account captured by the extension."""

    flow: str
    activity_url: str
    external_account_token: str = ""
    detected_account_name: str = ""
    financial_account_id: int | None = None


@dataclass(frozen=True)
class CapturedSession:
    """The full payload posted by the extension."""

    institution_slug: str
    login_id: str
    storage_state: dict | str
    accounts: tuple[CapturedAccount, ...]
    nickname: str = ""


def _serialize_storage_state(state) -> str:
    if isinstance(state, str):
        return state
    return json.dumps(state)


@transaction.atomic
def ingest_captured_session(user, capture: CapturedSession) -> BankConnection:
    """Create or update a ``BankConnection`` from the extension payload.

    Idempotent on ``(user, institution, login_id)`` so re-captures from the
    same login refresh the cookies in place. Per-account links are upserted
    by ``external_account_token`` (or by ``activity_url`` as a fallback).
    """

    institution = FinancialInstitution.objects.filter(slug=capture.institution_slug).first()
    if institution is None:
        # Some deployments seed institutions by name without a slug. Match
        # by name as a fallback before creating a duplicate.
        pretty_name = capture.institution_slug.replace("_", " ").title()
        institution = FinancialInstitution.objects.filter(name__iexact=pretty_name).first()
        if institution is not None and not institution.slug:
            institution.slug = capture.institution_slug
            institution.save(update_fields=["slug"])
        elif institution is None:
            institution = FinancialInstitution.objects.create(
                name=pretty_name,
                slug=capture.institution_slug,
            )
            logger.info("Created FinancialInstitution {} on first capture", institution.slug)

    connection, created = BankConnection.objects.get_or_create(
        user=user,
        institution=institution,
        login_id=capture.login_id,
        defaults={
            "nickname": capture.nickname or institution.name,
            "status": "active",
        },
    )

    if not created:
        connection.status = "active"
        connection.consecutive_failures = 0
        connection.last_failure_reason = ""
        if capture.nickname:
            connection.nickname = capture.nickname
        connection.save(
            update_fields=["status", "consecutive_failures", "last_failure_reason", "nickname", "updated_at"]
        )

    session, _ = BankSession.objects.get_or_create(
        connection=connection,
        defaults={"storage_state_blob": ""},
    )
    session.set_storage_state(_serialize_storage_state(capture.storage_state))
    session.captured_at = timezone.now()
    session.last_validated_at = timezone.now()
    session.save()

    _upsert_account_links(user, connection, capture.accounts)

    if connection.next_run_at is None:
        reschedule(connection)

    return connection


def _upsert_account_links(
    user, connection: BankConnection, captured: Iterable[CapturedAccount]
) -> list[BankAccountLink]:
    """Create/update ``BankAccountLink`` rows from captured accounts.

    Captured accounts can include a ``financial_account_id`` to bind directly
    to an existing Richtato account, or omit it for a "session-only" capture
    where the user will pick the account in the UI later.
    """

    results: list[BankAccountLink] = []
    for account in captured:
        match = None
        if account.external_account_token:
            match = BankAccountLink.objects.filter(
                connection=connection,
                external_account_token=account.external_account_token,
            ).first()
        if match is None and account.financial_account_id:
            match = BankAccountLink.objects.filter(
                connection=connection,
                financial_account_id=account.financial_account_id,
            ).first()

        financial_account = None
        if account.financial_account_id:
            financial_account = FinancialAccount.objects.filter(id=account.financial_account_id, user=user).first()

        if match is None:
            # Always create a link, even when the user did not yet pick a
            # Richtato FinancialAccount. The frontend lets them bind it
            # later, and the runner skips unbound links with a clear
            # message until then.
            link = BankAccountLink(connection=connection, financial_account=financial_account)
        else:
            link = match
            if financial_account is not None and link.financial_account_id != financial_account.id:
                link.financial_account = financial_account

        link.flow = account.flow or link.flow or "deposit"
        if account.activity_url:
            link.activity_url = account.activity_url
        if account.external_account_token:
            link.external_account_token = account.external_account_token
        if account.detected_account_name:
            link.detected_account_name = account.detected_account_name
        link.enabled = True
        link.save()
        results.append(link)

    return results


def disable_connection(connection: BankConnection) -> BankConnection:
    """Pause automation without deleting cookies."""

    connection.status = "disabled"
    connection.next_run_at = None
    connection.save(update_fields=["status", "next_run_at", "updated_at"])
    return connection


def reauth_required(connection: BankConnection, reason: str) -> BankConnection:
    """Mark the connection as needing fresh cookies."""

    connection.status = "reauth_required"
    connection.last_failure_reason = reason
    connection.next_run_at = None
    connection.save(update_fields=["status", "last_failure_reason", "next_run_at", "updated_at"])
    return connection


def record_run_outcome(
    connection: BankConnection,
    run: BankAutomationRun,
    *,
    succeeded: bool,
    failure_kind: str = "",
    failure_reason: str = "",
) -> None:
    """Update ``connection`` and recompute the next scheduled run.

    Triggers a transactional email the first time a connection transitions
    into ``reauth_required`` and once we cross the repeated-failure
    threshold, so the user notices before silently missing imports.
    """

    previous_status = connection.status
    previous_failures = connection.consecutive_failures or 0
    now = timezone.now()
    connection.last_run_at = now
    if succeeded:
        connection.last_success_at = now
        connection.consecutive_failures = 0
        connection.last_failure_reason = ""
        if connection.status not in {"disabled"}:
            connection.status = "active"
    else:
        connection.consecutive_failures = (connection.consecutive_failures or 0) + 1
        connection.last_failure_reason = failure_reason or failure_kind
        if failure_kind == "session_expired":
            connection.status = "reauth_required"
            connection.next_run_at = None
        elif connection.consecutive_failures >= 3:
            connection.status = "error"

    if connection.status == "active":
        reschedule(connection, save=False)

    connection.save()

    run.finished_at = now
    run.status = "completed" if succeeded else "failed"
    if not succeeded:
        run.failure_kind = failure_kind or "unknown"
        run.failure_reason = failure_reason
    run.save()

    # Best-effort notifications. Do not fail the run if the email backend is
    # misconfigured.
    try:
        # Only email on the transition into a problem state — do not nag every cycle.
        from apps.bank_automation.services import notifications

        if connection.status == "reauth_required" and previous_status != "reauth_required":
            notifications.send_reauth_required_email(connection)
        elif (
            connection.status == "error"
            and previous_status != "error"
            and connection.consecutive_failures >= 3
            and previous_failures < 3
        ):
            notifications.send_repeated_failure_email(connection)
    except Exception:
        logger.exception(
            "Failed to send notification for connection={} status={}",
            connection.id,
            connection.status,
        )
