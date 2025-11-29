from apps.category.models import Category
from rest_framework import serializers

from .models import UserPreference


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "enabled"]

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
