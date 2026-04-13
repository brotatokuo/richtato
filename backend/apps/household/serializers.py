"""Serializers for household API."""

from rest_framework import serializers

from apps.household.models import Household, HouseholdMember


class HouseholdMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = HouseholdMember
        fields = ["user_id", "username", "joined_at"]


class HouseholdSerializer(serializers.ModelSerializer):
    members = HouseholdMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Household
        fields = ["id", "name", "members", "created_at"]
        read_only_fields = ["id", "created_at"]


class HouseholdCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class JoinHouseholdSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)
