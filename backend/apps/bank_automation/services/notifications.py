"""Per-user email notifications for bank automation events.

Phase 2 ships transactional emails for the two user-actionable states:

* ``reauth_required`` — user must re-capture cookies via the Chrome extension.
* repeated ``error`` runs — user should investigate or disable the connection.

Emails are sent through Django's email backend, so the deployment can swap
SMTP / SES / Mailgun without touching this file. Local dev defaults to the
``console`` backend (``EMAIL_BACKEND`` setting) so messages just print.

To avoid notification spam, we only email once per "transition into the
state" — the connection's ``status`` is the de-duplication key, augmented
by ``last_failure_reason`` so we re-send if the failure mode changes.
"""

from __future__ import annotations

import os

from django.core.mail import send_mail
from loguru import logger

from apps.bank_automation.models import BankConnection


def _from_email() -> str:
    return os.getenv("BANK_AUTOMATION_FROM_EMAIL", "no-reply@richtato.local")


def _app_base_url() -> str:
    return os.getenv("RICHTATO_APP_BASE_URL", "http://localhost:3000").rstrip("/")


def send_reauth_required_email(connection: BankConnection) -> bool:
    """Email the connection owner asking them to refresh the bank session.

    Returns True when the email was sent (or printed via the console backend)
    and False when the user has no email address on file.
    """

    user = connection.user
    if not user.email:
        logger.info("Skipping reauth email for connection={}: user has no email", connection.id)
        return False

    subject = f"[Richtato] Refresh your {connection.institution.name} session"
    app_url = _app_base_url()
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your saved {connection.institution.name} session expired, so Richtato\n"
        f"could not download your latest transactions.\n\n"
        f"To resume automatic downloads:\n"
        f"  1. Open Chrome and go to your bank.\n"
        f"  2. Sign in with your password and any MFA.\n"
        f"  3. Click the Richtato extension icon and press 'Sync this account'.\n\n"
        f"Or open Richtato to review the connection:\n"
        f"  {app_url}/bank-automation\n\n"
        f"Last attempted run: {connection.last_run_at or 'unknown'}\n"
        f"Reason: {connection.last_failure_reason or 'session expired'}\n"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=_from_email(),
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send reauth email to {} (connection={})",
            user.email,
            connection.id,
        )
        return False

    logger.info("Sent reauth email to {} (connection={})", user.email, connection.id)
    return True


def send_repeated_failure_email(connection: BankConnection) -> bool:
    """Email the user when a connection has crossed the failure threshold."""

    user = connection.user
    if not user.email:
        return False

    subject = f"[Richtato] {connection.institution.name} sync keeps failing"
    app_url = _app_base_url()
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Richtato's automation has now failed {connection.consecutive_failures} times in a row\n"
        f"for your {connection.institution.name} connection.\n\n"
        f"Open Richtato to review the run history and either retry or disable\n"
        f"the connection:\n"
        f"  {app_url}/bank-automation\n\n"
        f"Last error: {connection.last_failure_reason or 'unknown'}\n"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=_from_email(),
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send repeated-failure email to {} (connection={})",
            user.email,
            connection.id,
        )
        return False

    logger.info(
        "Sent repeated-failure email to {} (connection={})",
        user.email,
        connection.id,
    )
    return True
