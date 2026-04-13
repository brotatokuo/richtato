"""Tests for Household models."""

import pytest
from django.db import IntegrityError

from apps.household.models import Household, HouseholdMember


class TestHousehold:
    def test_create_household(self, user_a):
        h = Household.objects.create(name="Smith Family", created_by=user_a)
        assert h.id is not None
        assert h.name == "Smith Family"
        assert h.created_by == user_a

    def test_str_representation(self, user_a):
        h = Household.objects.create(name="Smith Family", created_by=user_a)
        assert str(h) == "Smith Family"

    def test_invite_code_unique_constraint(self, user_a, user_b):
        Household.objects.create(name="H1", created_by=user_a, invite_code="ABC12345")
        with pytest.raises(IntegrityError):
            Household.objects.create(name="H2", created_by=user_b, invite_code="ABC12345")

    def test_household_members_related_name(self, household, user_a):
        members = list(household.members.all())
        assert len(members) == 1
        assert members[0].user == user_a


class TestHouseholdMember:
    def test_create_membership(self, user_a):
        h = Household.objects.create(name="Test", created_by=user_a)
        m = HouseholdMember.objects.create(household=h, user=user_a)
        assert m.household == h
        assert m.user == user_a

    def test_user_can_only_join_one_household(self, household, user_a, user_b):
        h2 = Household.objects.create(name="Another", created_by=user_b)
        with pytest.raises(IntegrityError):
            HouseholdMember.objects.create(household=h2, user=user_a)

    def test_joined_at_auto_set(self, household, user_b):
        m = HouseholdMember.objects.create(household=household, user=user_b)
        assert m.joined_at is not None

    def test_cascade_delete_household(self, household, user_a):
        assert HouseholdMember.objects.filter(user=user_a).exists()
        household.delete()
        assert not HouseholdMember.objects.filter(user=user_a).exists()

    def test_cascade_delete_user(self, db):
        from apps.richtato_user.models import User

        temp_user = User.objects.create_user(username="temp", password="pass")
        h = Household.objects.create(name="Temp", created_by=temp_user)
        HouseholdMember.objects.create(household=h, user=temp_user)
        temp_user.delete()
        assert not HouseholdMember.objects.filter(user_id=temp_user.id).exists()
