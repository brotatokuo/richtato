"""Transactional email via Resend HTTP API."""

from __future__ import annotations

import requests
from django.conf import settings
from loguru import logger

RESEND_EMAILS_URL = "https://api.resend.com/emails"


class EmailService:
    """Thin Resend client; skips send when API key or from-address is unset."""

    @classmethod
    def is_configured(cls) -> bool:
        return bool(getattr(settings, "RESEND_API_KEY", "") and getattr(settings, "RESEND_FROM_EMAIL", ""))

    @classmethod
    def send(
        cls,
        *,
        to: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> bool:
        """Send one email. Returns True on success, False when skipped or failed."""
        if not to:
            logger.warning("Email send skipped: empty recipient")
            return False
        if not cls.is_configured():
            logger.warning("Resend not configured; skipping email to {}", to)
            return False

        payload: dict[str, object] = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "text": text,
        }
        if html:
            payload["html"] = html

        try:
            response = requests.post(
                RESEND_EMAILS_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.exception("Resend request failed for {}: {}", to, exc)
            return False

        if response.status_code >= 400:
            logger.error(
                "Resend API error status={} body={}",
                response.status_code,
                response.text[:500],
            )
            return False

        logger.info("Resend email sent to {} subject={!r}", to, subject)
        return True
