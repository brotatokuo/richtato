"""Repository for Household models."""

from apps.household.models import Household, HouseholdMember
from apps.richtato_user.models import User


class HouseholdRepository:
    """Data access for household operations."""

    def get_by_id(self, household_id: int) -> Household | None:
        try:
            return Household.objects.prefetch_related("members__user").get(id=household_id)
        except Household.DoesNotExist:
            return None

    def get_by_user(self, user: User) -> Household | None:
        """Get the household a user belongs to, or None."""
        try:
            membership = HouseholdMember.objects.select_related("household").get(user=user)
            return (
                Household.objects.prefetch_related("members__user")
                .get(id=membership.household_id)
            )
        except HouseholdMember.DoesNotExist:
            return None

    def get_by_invite_code(self, code: str) -> Household | None:
        try:
            return Household.objects.prefetch_related("members__user").get(invite_code=code)
        except Household.DoesNotExist:
            return None

    def create_household(self, name: str, created_by: User) -> Household:
        return Household.objects.create(name=name, created_by=created_by)

    def add_member(self, household: Household, user: User) -> HouseholdMember:
        return HouseholdMember.objects.create(household=household, user=user)

    def remove_member(self, user: User) -> None:
        HouseholdMember.objects.filter(user=user).delete()

    def get_member_count(self, household: Household) -> int:
        return HouseholdMember.objects.filter(household=household).count()

    def get_member_user_ids(self, household: Household) -> list[int]:
        return list(household.members.values_list("user_id", flat=True))

    def delete_household(self, household: Household) -> None:
        household.delete()

    def update_household(self, household: Household, **kwargs) -> Household:
        for key, value in kwargs.items():
            setattr(household, key, value)
        household.save()
        return household
