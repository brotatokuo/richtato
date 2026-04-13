"""Tests for HouseholdService."""

import re
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.household.models import Household, HouseholdMember
from apps.household.services.household_service import HouseholdService


@pytest.fixture
def service():
    return HouseholdService()


class TestCreateHousehold:
    def test_creates_household_and_adds_creator_as_member(self, service, user_a):
        h = service.create_household(user_a, "Our House")
        assert h.name == "Our House"
        assert h.created_by == user_a
        assert h.members.filter(user=user_a).exists()

    def test_raises_if_user_already_in_household(self, service, user_a, household):
        with pytest.raises(ValueError, match="already a member"):
            service.create_household(user_a, "Another")


class TestGenerateInviteCode:
    def test_generates_8_char_alphanumeric_code(self, service, user_a, household):
        result = service.generate_invite_code(user_a)
        assert re.match(r"^[A-Z0-9]{8}$", result["invite_code"])

    def test_sets_expiry_48_hours_from_now(self, service, user_a, household):
        result = service.generate_invite_code(user_a)
        expected = timezone.now() + timedelta(hours=48)
        assert abs((result["expires_at"] - expected).total_seconds()) < 5

    def test_replaces_existing_code(self, service, user_a, household):
        result1 = service.generate_invite_code(user_a)
        result2 = service.generate_invite_code(user_a)
        assert result1["invite_code"] != result2["invite_code"]

    def test_raises_if_user_not_in_household(self, service, user_b):
        with pytest.raises(ValueError, match="not a member"):
            service.generate_invite_code(user_b)


class TestJoinHousehold:
    def test_joins_with_valid_code(self, service, user_a, user_b, household):
        result = service.generate_invite_code(user_a)
        code = result["invite_code"]
        h = service.join_household(user_b, code)
        assert h.members.filter(user=user_b).exists()

    def test_rejects_expired_code(self, service, user_a, user_b, household):
        result = service.generate_invite_code(user_a)
        household.refresh_from_db()
        household.invite_code_expires_at = timezone.now() - timedelta(hours=1)
        household.save(update_fields=["invite_code_expires_at"])
        with pytest.raises(ValueError, match="expired"):
            service.join_household(user_b, result["invite_code"])

    def test_rejects_invalid_code(self, service, user_b):
        with pytest.raises(ValueError, match="Invalid"):
            service.join_household(user_b, "BADCODE1")

    def test_rejects_if_household_full(self, service, user_a, user_b, user_c, household_with_both):
        h2 = Household.objects.create(name="H2", created_by=user_c, invite_code="FULL1234")
        h2.invite_code_expires_at = timezone.now() + timedelta(hours=48)
        h2.save()
        HouseholdMember.objects.create(household=h2, user=user_c)
        temp_user = type(user_a).objects.create_user(username="temp_full", password="p")
        HouseholdMember.objects.create(household=h2, user=temp_user)
        yet_another = type(user_a).objects.create_user(username="yet_another", password="p")
        with pytest.raises(ValueError, match="full"):
            service.join_household(yet_another, "FULL1234")

    def test_rejects_if_user_already_in_a_household(self, service, user_a, user_b, household):
        result = service.generate_invite_code(user_a)
        h2 = Household.objects.create(name="H2", created_by=user_b)
        HouseholdMember.objects.create(household=h2, user=user_b)
        with pytest.raises(ValueError, match="already a member"):
            service.join_household(user_b, result["invite_code"])

    def test_code_cleared_after_use(self, service, user_a, user_b, household):
        result = service.generate_invite_code(user_a)
        code = result["invite_code"]
        service.join_household(user_b, code)
        household.refresh_from_db()
        assert household.invite_code is None
        assert household.invite_code_expires_at is None


class TestLeaveHousehold:
    def test_removes_membership(self, service, user_a, user_b, household_with_both):
        service.leave_household(user_b)
        assert not HouseholdMember.objects.filter(user=user_b).exists()

    def test_deletes_household_if_last_member(self, service, user_a, household):
        hid = household.id
        service.leave_household(user_a)
        assert not Household.objects.filter(id=hid).exists()

    def test_household_persists_if_partner_remains(self, service, user_a, user_b, household_with_both):
        hid = household_with_both.id
        service.leave_household(user_b)
        assert Household.objects.filter(id=hid).exists()


class TestGetHousehold:
    def test_returns_household_for_member(self, service, user_a, household):
        result = service.get_household(user_a)
        assert result is not None
        assert result.id == household.id

    def test_returns_none_for_non_member(self, service, user_b):
        result = service.get_household(user_b)
        assert result is None
