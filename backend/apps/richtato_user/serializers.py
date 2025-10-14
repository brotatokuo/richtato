from rest_framework import serializers

from .models import Category, UserPreference


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "enabled"]

        read_only_fields = ["id"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ["theme", "currency", "date_format"]
