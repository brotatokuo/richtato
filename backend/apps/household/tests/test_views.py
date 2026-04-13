"""Tests for household API views."""

import pytest
from rest_framework.test import APIClient

from apps.household.models import HouseholdMember


@pytest.fixture
def api_client():
    return APIClient()


class TestCreateHouseholdView:
    def test_creates_household(self, api_client, user_a):
        api_client.force_authenticate(user=user_a)
        response = api_client.post("/api/v1/household/", {"name": "Our House"}, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Our House"
        assert len(response.data["members"]) == 1

    def test_second_create_returns_400(self, api_client, user_a, household):
        api_client.force_authenticate(user=user_a)
        response = api_client.post("/api/v1/household/", {"name": "Another"}, format="json")
        assert response.status_code == 400


class TestGetHouseholdView:
    def test_returns_household(self, api_client, user_a, household):
        api_client.force_authenticate(user=user_a)
        response = api_client.get("/api/v1/household/")
        assert response.status_code == 200
        assert response.data["name"] == "Test Household"

    def test_returns_404_without_household(self, api_client, user_b):
        api_client.force_authenticate(user=user_b)
        response = api_client.get("/api/v1/household/")
        assert response.status_code == 404


class TestInviteView:
    def test_returns_invite_code(self, api_client, user_a, household):
        api_client.force_authenticate(user=user_a)
        response = api_client.post("/api/v1/household/invite/")
        assert response.status_code == 200
        assert len(response.data["invite_code"]) == 8

    def test_returns_400_without_household(self, api_client, user_b):
        api_client.force_authenticate(user=user_b)
        response = api_client.post("/api/v1/household/invite/")
        assert response.status_code == 400


class TestJoinView:
    def test_join_with_valid_code(self, api_client, user_a, user_b, household):
        api_client.force_authenticate(user=user_a)
        invite_resp = api_client.post("/api/v1/household/invite/")
        code = invite_resp.data["invite_code"]

        api_client.force_authenticate(user=user_b)
        response = api_client.post("/api/v1/household/join/", {"code": code}, format="json")
        assert response.status_code == 200
        assert len(response.data["members"]) == 2

    def test_invalid_code_returns_400(self, api_client, user_b):
        api_client.force_authenticate(user=user_b)
        response = api_client.post("/api/v1/household/join/", {"code": "INVALID1"}, format="json")
        assert response.status_code == 400


class TestLeaveView:
    def test_leave_removes_membership(self, api_client, user_b, household_with_both):
        api_client.force_authenticate(user=user_b)
        response = api_client.post("/api/v1/household/leave/")
        assert response.status_code == 200
        assert not HouseholdMember.objects.filter(user=user_b).exists()


class TestMembersView:
    def test_returns_member_list(self, api_client, user_a, user_b, household_with_both):
        api_client.force_authenticate(user=user_a)
        response = api_client.get("/api/v1/household/members/")
        assert response.status_code == 200
        usernames = [m["username"] for m in response.data["members"]]
        assert "user_a" in usernames
        assert "user_b" in usernames
