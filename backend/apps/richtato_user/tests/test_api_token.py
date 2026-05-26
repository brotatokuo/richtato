"""Tests for the bank-agent API token endpoint."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="apitoken", email="apitoken@test.com", password="x")


class TestAPIAgentTokenView:
    def test_returns_token_and_fernet_key_for_authenticated_user(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("api_token"))

        assert response.status_code == 200
        payload = response.json()
        token = payload["token"]
        fernet_key = payload["fernet_key"]
        assert isinstance(token, str) and token
        assert isinstance(fernet_key, str) and fernet_key

        second = client.get(reverse("api_token"))
        assert second.json()["token"] == token
        assert second.json()["fernet_key"] == fernet_key

    def test_requires_authentication(self):
        client = APIClient()
        response = client.get(reverse("api_token"))
        assert response.status_code in {401, 403}
