"""Serializers for bank automation API."""

from __future__ import annotations

from rest_framework import serializers

from apps.bank_automation.models import (
    BankAccountLink,
    BankAutomationRun,
    BankConnection,
)


class BankAccountLinkSerializer(serializers.ModelSerializer):
    """Per-account link, never exposes the encrypted activity URL."""

    financial_account_name = serializers.CharField(source="financial_account.name", read_only=True)
    financial_account_type = serializers.CharField(source="financial_account.account_type", read_only=True)

    class Meta:
        model = BankAccountLink
        fields = [
            "id",
            "financial_account",
            "financial_account_name",
            "financial_account_type",
            "flow",
            "external_account_token",
            "detected_account_name",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BankConnectionSerializer(serializers.ModelSerializer):
    """Read serializer for a connection, including account links."""

    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_slug = serializers.CharField(source="institution.slug", read_only=True)
    account_links = BankAccountLinkSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    cadence_display = serializers.CharField(source="get_cadence_display", read_only=True)

    class Meta:
        model = BankConnection
        fields = [
            "id",
            "institution",
            "institution_name",
            "institution_slug",
            "login_id",
            "nickname",
            "status",
            "status_display",
            "cadence",
            "cadence_display",
            "preferred_run_hour_local",
            "last_run_at",
            "last_success_at",
            "next_run_at",
            "consecutive_failures",
            "last_failure_reason",
            "next_reauth_estimated_at",
            "account_links",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "institution",
            "institution_name",
            "institution_slug",
            "login_id",
            "status",
            "status_display",
            "last_run_at",
            "last_success_at",
            "next_run_at",
            "consecutive_failures",
            "last_failure_reason",
            "next_reauth_estimated_at",
            "account_links",
            "created_at",
            "updated_at",
        ]


class BankConnectionUpdateSerializer(serializers.Serializer):
    """Patchable fields for a connection."""

    cadence = serializers.ChoiceField(choices=[c[0] for c in BankConnection.CADENCE_CHOICES], required=False)
    preferred_run_hour_local = serializers.IntegerField(min_value=0, max_value=23, required=False)
    nickname = serializers.CharField(max_length=120, required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False)


class CapturedAccountSerializer(serializers.Serializer):
    """One account inside an extension capture payload."""

    flow = serializers.ChoiceField(choices=["deposit", "credit_card"], default="deposit")
    activity_url = serializers.CharField()
    external_account_token = serializers.CharField(required=False, allow_blank=True)
    detected_account_name = serializers.CharField(required=False, allow_blank=True)
    financial_account_id = serializers.IntegerField(required=False, allow_null=True)


class CaptureSessionSerializer(serializers.Serializer):
    """The full payload posted by the Chrome extension."""

    institution_slug = serializers.CharField(max_length=64)
    login_id = serializers.CharField(max_length=120)
    storage_state = serializers.JSONField()
    accounts = CapturedAccountSerializer(many=True)
    nickname = serializers.CharField(max_length=120, required=False, allow_blank=True)


class BankAutomationRunSerializer(serializers.ModelSerializer):
    """Run history record."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = BankAutomationRun
        fields = [
            "id",
            "connection",
            "started_at",
            "finished_at",
            "status",
            "status_display",
            "failure_kind",
            "failure_reason",
            "accounts_attempted",
            "accounts_succeeded",
            "statements_imported",
            "triggered_by",
            "duration_seconds",
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj):
        return obj.duration_seconds


class BankAccountLinkUpdateSerializer(serializers.Serializer):
    """Per-account link toggles."""

    enabled = serializers.BooleanField(required=False)
    financial_account_id = serializers.IntegerField(required=False)
