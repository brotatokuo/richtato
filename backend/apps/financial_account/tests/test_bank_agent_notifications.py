"""Tests for bank-agent failure notifications."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import InAppNotification
from apps.richtato_user.models import User, UserPreference


@pytest.fixture
def user(db):
    return User.objects.create_user(username="notifyuser", email="notify@test.com", password="x")


def test_bank_agent_event_creates_in_app_notification(user):
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse("account-bank-agent-events"),
        {
            "event_type": "scheduled_download",
            "login_id": 7,
            "institution_slug": "bofa",
            "nickname": "personal",
            "failure_kind": "needs_reauth",
            "message": "Redirected to sign-in",
        },
        format="json",
    )

    assert response.status_code == 201
    notification = InAppNotification.objects.get(user=user)
    assert notification.source == "bank_sync"
    assert notification.severity == "warning"
    assert "re-auth" in notification.title
    assert "Redirected" in notification.body


def test_bank_agent_event_respects_email_opt_in(user, settings):
    settings.RESEND_API_KEY = "re_test"
    settings.RESEND_FROM_EMAIL = "Richtato <sync@test.com>"
    UserPreference.objects.filter(user=user).update(bank_sync_email_notifications=True)
    client = APIClient()
    client.force_authenticate(user=user)
    with patch("apps.core.services.notification_service.EmailService.send", return_value=True) as send:
        response = client.post(
            reverse("account-bank-agent-events"),
            {
                "event_type": "manual_download",
                "login_id": 7,
                "failure_kind": "no_download",
                "message": "No file was produced",
            },
            format="json",
        )

    assert response.status_code == 201
    send.assert_called_once()


def test_bank_agent_event_deduplicates_recent_failures(user):
    client = APIClient()
    client.force_authenticate(user=user)
    payload = {
        "event_type": "scheduled_download",
        "login_id": 7,
        "failure_kind": "no_download",
        "message": "No file was produced",
    }

    first = client.post(reverse("account-bank-agent-events"), payload, format="json")
    second = client.post(reverse("account-bank-agent-events"), payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert InAppNotification.objects.filter(user=user).count() == 1
    assert second.json()["created"] is False
