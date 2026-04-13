"""Service for household business logic."""

import secrets
import string
from datetime import timedelta

from django.utils import timezone

from apps.household.models import Household
from apps.household.repositories.household_repository import HouseholdRepository
from apps.richtato_user.models import User

MAX_HOUSEHOLD_MEMBERS = 2
INVITE_CODE_LENGTH = 8
INVITE_CODE_EXPIRY_HOURS = 48


class HouseholdService:
    """Business logic for household management."""

    def __init__(self):
        self.repository = HouseholdRepository()

    def get_household(self, user: User) -> Household | None:
        return self.repository.get_by_user(user)

    def create_household(self, user: User, name: str) -> Household:
        existing = self.repository.get_by_user(user)
        if existing:
            raise ValueError("You are already a member of a household.")

        household = self.repository.create_household(name=name, created_by=user)
        self.repository.add_member(household, user)
        return household

    def generate_invite_code(self, user: User) -> dict:
        household = self.repository.get_by_user(user)
        if not household:
            raise ValueError("You are not a member of any household.")

        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(INVITE_CODE_LENGTH))
        expires_at = timezone.now() + timedelta(hours=INVITE_CODE_EXPIRY_HOURS)

        self.repository.update_household(
            household, invite_code=code, invite_code_expires_at=expires_at,
        )

        return {"invite_code": code, "expires_at": expires_at}

    def join_household(self, user: User, invite_code: str) -> Household:
        existing = self.repository.get_by_user(user)
        if existing:
            raise ValueError("You are already a member of a household.")

        household = self.repository.get_by_invite_code(invite_code)
        if not household:
            raise ValueError("Invalid invite code.")

        if household.invite_code_expires_at and household.invite_code_expires_at < timezone.now():
            raise ValueError("Invite code has expired.")

        member_count = self.repository.get_member_count(household)
        if member_count >= MAX_HOUSEHOLD_MEMBERS:
            raise ValueError("This household is already full.")

        self.repository.add_member(household, user)

        self.repository.update_household(
            household, invite_code=None, invite_code_expires_at=None,
        )

        return self.repository.get_by_id(household.id)

    def leave_household(self, user: User) -> None:
        household = self.repository.get_by_user(user)
        if not household:
            raise ValueError("You are not a member of any household.")

        self.repository.remove_member(user)

        remaining = self.repository.get_member_count(household)
        if remaining == 0:
            self.repository.delete_household(household)

    def get_members(self, user: User) -> list[dict]:
        household = self.repository.get_by_user(user)
        if not household:
            return []

        return [
            {
                "id": m.user.id,
                "username": m.user.username,
                "joined_at": m.joined_at,
            }
            for m in household.members.select_related("user").all()
        ]

    def get_household_member_ids(self, user: User) -> list[int]:
        household = self.repository.get_by_user(user)
        if not household:
            return [user.id]
        return self.repository.get_member_user_ids(household)
