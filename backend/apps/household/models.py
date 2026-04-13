"""Household models for couples/family finance tracking."""

from django.conf import settings
from django.db import models


class Household(models.Model):
    """A household unit (e.g. a couple) that can share financial data."""

    name = models.CharField(max_length=100, help_text="Household display name")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_households",
    )
    invite_code = models.CharField(
        max_length=32, unique=True, null=True, blank=True,
        help_text="Single-use invite code for joining",
    )
    invite_code_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "household"

    def __str__(self):
        return self.name


class HouseholdMember(models.Model):
    """Links a user to exactly one household."""

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="members",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="household_membership",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "household_member"

    def __str__(self):
        return f"{self.user.username} in {self.household.name}"
