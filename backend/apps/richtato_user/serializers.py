from apps.transaction.models import TransactionCategory
from rest_framework import serializers

from .models import UserPreference


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for TransactionCategory model."""

    class Meta:
        model = TransactionCategory
        fields = ["id", "name", "slug", "is_income", "is_expense", "icon", "color"]
        read_only_fields = ["id"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "theme",
            "currency",
            "date_format",
            "timezone",
            "notifications_enabled",
        ]
