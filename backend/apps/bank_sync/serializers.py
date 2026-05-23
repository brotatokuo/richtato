"""Serializers for the bank sync API."""

from __future__ import annotations

from rest_framework import serializers

from apps.bank_sync.models import BankLogin, SyncedAccount, SyncRun


class SyncedAccountSerializer(serializers.ModelSerializer):
    """Per-account binding, never exposes the encrypted activity URL."""

    financial_account_name = serializers.CharField(source="financial_account.name", read_only=True)
    financial_account_type = serializers.CharField(source="financial_account.account_type", read_only=True)

    class Meta:
        model = SyncedAccount
        fields = [
            "id",
            "bank_login",
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


class BankLoginSerializer(serializers.ModelSerializer):
    """Read serializer for a bank login."""

    institution_name = serializers.CharField(source="institution.name", read_only=True)
    institution_slug = serializers.CharField(source="institution.slug", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    cadence_display = serializers.CharField(source="get_cadence_display", read_only=True)
    synced_accounts = SyncedAccountSerializer(many=True, read_only=True)

    class Meta:
        model = BankLogin
        fields = [
            "id",
            "institution",
            "institution_name",
            "institution_slug",
            "nickname",
            "status",
            "status_display",
            "cadence",
            "cadence_display",
            "preferred_run_hour_local",
            "cookies_captured_at",
            "cookies_expected_to_expire_at",
            "last_run_at",
            "last_success_at",
            "next_run_at",
            "consecutive_failures",
            "last_failure_reason",
            "synced_accounts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "institution_name",
            "institution_slug",
            "status",
            "status_display",
            "cookies_captured_at",
            "cookies_expected_to_expire_at",
            "last_run_at",
            "last_success_at",
            "next_run_at",
            "consecutive_failures",
            "last_failure_reason",
            "synced_accounts",
            "created_at",
            "updated_at",
        ]


class BankLoginCreateSerializer(serializers.Serializer):
    """Payload to create a new ``BankLogin``."""

    institution = serializers.IntegerField(help_text="FinancialInstitution id")
    nickname = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    cadence = serializers.ChoiceField(
        choices=[c[0] for c in BankLogin.CADENCE_CHOICES],
        required=False,
        default="daily",
    )
    preferred_run_hour_local = serializers.IntegerField(min_value=0, max_value=23, required=False, default=6)


class BankLoginUpdateSerializer(serializers.Serializer):
    """Patchable fields for a bank login."""

    cadence = serializers.ChoiceField(choices=[c[0] for c in BankLogin.CADENCE_CHOICES], required=False)
    preferred_run_hour_local = serializers.IntegerField(min_value=0, max_value=23, required=False)
    nickname = serializers.CharField(max_length=120, required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False)


class SyncedAccountBindSerializer(serializers.Serializer):
    """One row in the bulk-bind payload after the wizard's discovery step."""

    bank_login = serializers.IntegerField()
    financial_account = serializers.IntegerField()
    flow = serializers.ChoiceField(choices=[c[0] for c in SyncedAccount.FLOW_CHOICES])
    external_account_token = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    activity_url = serializers.CharField(required=False, allow_blank=True, default="")
    detected_account_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class SyncedAccountBulkBindSerializer(serializers.Serializer):
    accounts = SyncedAccountBindSerializer(many=True)


class SyncedAccountUpdateSerializer(serializers.Serializer):
    """Patchable fields for a synced account."""

    enabled = serializers.BooleanField(required=False)
    flow = serializers.ChoiceField(choices=[c[0] for c in SyncedAccount.FLOW_CHOICES], required=False)


class SyncRunSerializer(serializers.ModelSerializer):
    """Run history record."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    task_kind_display = serializers.CharField(source="get_task_kind_display", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = SyncRun
        fields = [
            "id",
            "bank_login",
            "task_kind",
            "task_kind_display",
            "status",
            "status_display",
            "triggered_by",
            "queued_at",
            "leased_at",
            "finished_at",
            "failure_kind",
            "failure_reason",
            "accounts_attempted",
            "accounts_succeeded",
            "statements_imported",
            "duration_seconds",
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj: SyncRun) -> float | None:
        return obj.duration_seconds


class CapturedAccountDiscoverySerializer(serializers.Serializer):
    """One discovered bank-side account the agent reports after headed login."""

    detected_account_name = serializers.CharField(max_length=255)
    external_account_token = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    activity_url = serializers.CharField(required=False, allow_blank=True, default="")
    flow = serializers.ChoiceField(choices=[c[0] for c in SyncedAccount.FLOW_CHOICES])


class CapturedSessionSerializer(serializers.Serializer):
    """Agent -> API payload after a headed interactive_login completes."""

    storage_state = serializers.JSONField()
    discovered_accounts = CapturedAccountDiscoverySerializer(many=True, required=False, default=list)


class RunOutcomeSerializer(serializers.Serializer):
    """Agent -> API payload reporting the outcome of a SyncRun."""

    succeeded = serializers.BooleanField()
    failure_kind = serializers.CharField(max_length=24, required=False, allow_blank=True, default="")
    failure_reason = serializers.CharField(required=False, allow_blank=True, default="")
    accounts_attempted = serializers.IntegerField(min_value=0, required=False, default=0)
    accounts_succeeded = serializers.IntegerField(min_value=0, required=False, default=0)
    statements_imported = serializers.IntegerField(min_value=0, required=False, default=0)
