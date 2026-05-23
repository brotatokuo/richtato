"""Views for the bank automation API."""

from __future__ import annotations

from django.utils import timezone
from loguru import logger
from rest_framework import status
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.bank_automation import audit
from apps.bank_automation.models import (
    BankAccountLink,
    BankAutomationRun,
    BankConnection,
)
from apps.bank_automation.serializers import (
    BankAccountLinkUpdateSerializer,
    BankAutomationRunSerializer,
    BankConnectionSerializer,
    BankConnectionUpdateSerializer,
    CaptureSessionSerializer,
)
from apps.bank_automation.services.connection_service import (
    CapturedAccount,
    CapturedSession,
    disable_connection,
    ingest_captured_session,
    record_run_outcome,
)
from apps.bank_automation.services.scheduling import reschedule
from apps.financial_account.models import FinancialAccount, FinancialInstitution


class _CaptureSessionThrottle(UserRateThrottle):
    """Per-user throttle on the extension's session-ingest endpoint.

    The Chrome extension submits at most a handful of captures per day under
    normal use; anything north of this rate suggests a misbehaving client or
    abuse. Override via ``DRF_THROTTLE_RATES`` if needed.
    """

    scope = "bank_automation_capture"

    def get_rate(self):
        return "30/hour"


class _ManualRunThrottle(UserRateThrottle):
    """Throttle the manual 'Sync now' endpoint to keep banks happy."""

    scope = "bank_automation_manual_run"

    def get_rate(self):
        return "30/hour"


class IsAutomationRunner(BasePermission):
    """Grants access only to accounts with ``is_automation_runner=True``.

    Used alongside ``IsAuthenticated`` on the internal runner endpoints so the
    automation container can query and act on connections across all users,
    while regular users are still rejected.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and getattr(request.user, "is_automation_runner", False)
        )


# Slugs of institutions for which a Playwright adapter exists today. Keep in
# sync with scripts/automation/institutions/.
SUPPORTED_ADAPTER_SLUGS = ("bofa", "chase", "marcus", "amex", "fidelity")


class _AuthMixin:
    """Shared auth config — accept session, token, and basic auth.

    Token auth lets the Chrome extension authenticate without sharing a
    session cookie across the bank's domain and Richtato's domain.
    """

    authentication_classes = [
        SessionAuthentication,
        TokenAuthentication,
        BasicAuthentication,
    ]
    permission_classes = [IsAuthenticated]


class BankConnectionListAPIView(_AuthMixin, APIView):
    """List the user's bank connections."""

    def get(self, request):
        connections = (
            BankConnection.objects.filter(user=request.user)
            .select_related("institution")
            .prefetch_related("account_links__financial_account")
        )
        serializer = BankConnectionSerializer(connections, many=True)
        return Response({"connections": serializer.data})


class BankConnectionDetailAPIView(_AuthMixin, APIView):
    """Retrieve / update / delete a single connection."""

    def _get(self, request, pk):
        return (
            BankConnection.objects.filter(user=request.user, pk=pk)
            .select_related("institution")
            .prefetch_related("account_links__financial_account")
            .first()
        )

    def get(self, request, pk):
        connection = self._get(request, pk)
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BankConnectionSerializer(connection).data)

    def patch(self, request, pk):
        connection = self._get(request, pk)
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BankConnectionUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        cadence_changed = "cadence" in data
        hour_changed = "preferred_run_hour_local" in data

        for field in ("cadence", "preferred_run_hour_local", "nickname"):
            if field in data:
                setattr(connection, field, data[field])

        if "enabled" in data:
            connection.status = "active" if data["enabled"] else "disabled"

        connection.save()

        if connection.status == "active" and (cadence_changed or hour_changed):
            reschedule(connection)
        elif connection.status != "active":
            connection.next_run_at = None
            connection.save(update_fields=["next_run_at", "updated_at"])

        connection.refresh_from_db()
        audit.audit(
            audit.EVENT_CONNECTION_UPDATED,
            user_id=request.user.id,
            connection_id=connection.id,
            request=request,
            summary=f"cadence={connection.cadence} hour={connection.preferred_run_hour_local}",
        )
        return Response(BankConnectionSerializer(connection).data)

    def delete(self, request, pk):
        connection = self._get(request, pk)
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        connection_id = connection.id
        connection.delete()
        audit.audit(
            audit.EVENT_CONNECTION_DELETED,
            user_id=request.user.id,
            connection_id=connection_id,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class BankConnectionDisableAPIView(_AuthMixin, APIView):
    """Pause automation without deleting cookies."""

    def post(self, request, pk):
        connection = BankConnection.objects.filter(user=request.user, pk=pk).first()
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        disable_connection(connection)
        audit.audit(
            audit.EVENT_CONNECTION_DISABLED,
            user_id=request.user.id,
            connection_id=connection.id,
            request=request,
        )
        return Response(BankConnectionSerializer(connection).data)


class BankConnectionRunAPIView(_AuthMixin, APIView):
    """Trigger an immediate run for the connection."""

    throttle_classes = [_ManualRunThrottle]

    def post(self, request, pk):
        connection = BankConnection.objects.filter(user=request.user, pk=pk).first()
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if connection.status not in {"active", "error"}:
            return Response(
                {"error": (f"Connection is {connection.status}; cannot run until reactivated")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Just bump the lease pointer. The automation worker creates the
        # actual ``BankAutomationRun`` row when it leases the connection
        # via /runner/due-connections/, so we don't double-create here.
        # ``triggered_by`` is recorded in the audit log + reflected by the
        # fact that the row's started_at lands close to ``next_run_at``.
        connection.next_run_at = timezone.now()
        connection.save(update_fields=["next_run_at", "updated_at"])

        logger.info("Manual run requested for bank_connection={}", connection.id)
        audit.audit(
            audit.EVENT_MANUAL_RUN_REQUESTED,
            user_id=request.user.id,
            connection_id=connection.id,
            request=request,
        )

        return Response(
            {"queued_at": connection.next_run_at.isoformat()},
            status=status.HTTP_202_ACCEPTED,
        )


class BankConnectionRunsAPIView(_AuthMixin, APIView):
    """Run history for a connection."""

    def get(self, request, pk):
        connection = BankConnection.objects.filter(user=request.user, pk=pk).first()
        if connection is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        runs = connection.runs.all()[:50]
        return Response({"runs": BankAutomationRunSerializer(runs, many=True).data})


class BankAccountLinkDetailAPIView(_AuthMixin, APIView):
    """PATCH or DELETE a single account link."""

    def patch(self, request, pk):
        link = (
            BankAccountLink.objects.filter(connection__user=request.user, pk=pk)
            .select_related("connection", "financial_account")
            .first()
        )
        if link is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BankAccountLinkUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if "enabled" in data:
            link.enabled = data["enabled"]
        if "financial_account_id" in data:
            account = FinancialAccount.objects.filter(user=request.user, id=data["financial_account_id"]).first()
            if account is None:
                return Response(
                    {"error": "Financial account not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            link.financial_account = account
        link.save()
        return Response({"id": link.id, "enabled": link.enabled})

    def delete(self, request, pk):
        link = BankAccountLink.objects.filter(connection__user=request.user, pk=pk).first()
        if link is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaptureSessionAPIView(_AuthMixin, APIView):
    """Endpoint the Chrome extension POSTs to with captured cookies + URLs."""

    throttle_classes = [_CaptureSessionThrottle]

    def post(self, request):
        serializer = CaptureSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        accounts = tuple(
            CapturedAccount(
                flow=a.get("flow", "deposit"),
                activity_url=a["activity_url"],
                external_account_token=a.get("external_account_token", ""),
                detected_account_name=a.get("detected_account_name", ""),
                financial_account_id=a.get("financial_account_id"),
            )
            for a in data["accounts"]
        )

        try:
            connection = ingest_captured_session(
                user=request.user,
                capture=CapturedSession(
                    institution_slug=data["institution_slug"],
                    login_id=data["login_id"],
                    storage_state=data["storage_state"],
                    accounts=accounts,
                    nickname=data.get("nickname", ""),
                ),
            )
        except Exception as exc:
            logger.exception("Failed to ingest bank automation capture")
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        audit.audit(
            audit.EVENT_SESSION_CAPTURED,
            user_id=request.user.id,
            connection_id=connection.id,
            request=request,
            summary=f"institution={connection.institution.slug} accounts={len(connection.account_links.all())}",
        )

        return Response(
            BankConnectionSerializer(connection).data,
            status=status.HTTP_201_CREATED,
        )


class SupportedInstitutionsAPIView(_AuthMixin, APIView):
    """List the institutions the runner can drive today."""

    def get(self, request):
        institutions = []
        deposit_capable = {"bofa", "chase", "marcus", "fidelity"}
        credit_capable = {"bofa", "chase", "amex"}
        for slug in SUPPORTED_ADAPTER_SLUGS:
            inst = FinancialInstitution.objects.filter(slug=slug).first()
            institutions.append(
                {
                    "slug": slug,
                    "name": inst.name if inst else slug.title(),
                    "supports_deposit": slug in deposit_capable,
                    "supports_credit_card": slug in credit_capable,
                }
            )
        return Response({"institutions": institutions})


class BindableAccountsAPIView(_AuthMixin, APIView):
    """List the user's Richtato accounts that the extension can offer to bind.

    Drives the dropdown in the Chrome extension popup so users pick an
    existing :class:`FinancialAccount` rather than typing a numeric id.

    Query parameters:
        institution_slug: When supplied, surfaces matching accounts first
            (and tags non-matching ones with ``matches_institution=False``).
            Accounts with no institution still come back so the user can
            still bind to one created without an institution association.

    Each entry includes:
        ``flow``                 derived from ``account_type``
        ``already_bound``        true when *any* active link references it
        ``already_bound_to``     id of the existing link/connection if so
    """

    def get(self, request):
        slug = (request.query_params.get("institution_slug") or "").strip().lower()

        accounts_qs = (
            FinancialAccount.objects.filter(user=request.user, is_active=True)
            .select_related("institution")
            .order_by("name")
        )

        existing_links = {
            link.financial_account_id: link
            for link in BankAccountLink.objects.filter(
                connection__user=request.user, financial_account__isnull=False
            ).select_related("connection")
        }

        accounts = []
        for account in accounts_qs:
            inst_slug = account.institution.slug if account.institution_id else ""
            inst_name = account.institution.name if account.institution_id else ""
            matches = bool(slug) and inst_slug == slug
            flow = "credit_card" if account.account_type == "credit_card" else "deposit"
            link = existing_links.get(account.id)
            accounts.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "account_type_display": account.get_account_type_display(),
                    "account_number_last4": account.account_number_last4 or "",
                    "institution_slug": inst_slug,
                    "institution_name": inst_name,
                    "flow": flow,
                    "matches_institution": matches,
                    "already_bound": link is not None,
                    "already_bound_link_id": link.id if link else None,
                    "already_bound_connection_id": link.connection_id if link else None,
                }
            )

        if slug:
            accounts.sort(
                key=lambda a: (
                    not a["matches_institution"],
                    a["already_bound"],
                    a["name"].lower(),
                )
            )

        return Response({"accounts": accounts})


class _RunnerPayloadMixin:
    """Helpers shared by the internal runner endpoints."""

    @staticmethod
    def _serialize_runner_connection(connection: BankConnection, run: BankAutomationRun) -> dict:
        """Build the JSON payload the runner consumes for one connection.

        Includes decrypted ``storage_state`` and per-account ``activity_url``
        so the runner can drive Playwright without round-tripping through
        another endpoint. Only the runner is expected to call this — the
        regular connection list endpoint never returns plaintext secrets.
        """

        session = getattr(connection, "session", None)
        storage_state = session.get_storage_state() if session else ""
        accounts = []
        for link in connection.account_links.filter(enabled=True).select_related("financial_account"):
            accounts.append(
                {
                    "link_id": link.id,
                    "slug": f"{connection.institution.slug}_{link.id}",
                    "flow": link.flow,
                    "activity_url": link.activity_url,
                    "external_account_token": link.external_account_token,
                    "detected_account_name": link.detected_account_name,
                    "financial_account_id": link.financial_account_id,
                    "institution_slug": connection.institution.slug,
                }
            )
        return {
            "connection_id": connection.id,
            "run_id": run.id,
            "user_id": connection.user_id,
            "institution_slug": connection.institution.slug,
            "login_id": connection.login_id,
            "nickname": connection.nickname,
            "storage_state": storage_state,
            "accounts": accounts,
        }


class RunnerDueConnectionsAPIView(_AuthMixin, _RunnerPayloadMixin, APIView):
    """Internal endpoint: fetch and lease due connections.

    Called by the automation container's scheduler every ~15 min. Returns
    decrypted ``storage_state`` and ``activity_url`` for every active
    connection whose ``next_run_at`` is in the past, and atomically opens a
    ``BankAutomationRun`` row so the runner can post the outcome back.

    When the caller has ``is_automation_runner=True`` the query spans all
    users, enabling one container to service a multi-tenant deployment.
    Regular authenticated users only see their own connections.
    """

    permission_classes = [IsAuthenticated | IsAutomationRunner]

    def get(self, request):
        now = timezone.now()
        force_all = str(request.query_params.get("all", "")).lower() in {"1", "true", "yes"}

        if getattr(request.user, "is_automation_runner", False):
            base_qs = BankConnection.objects.filter(status="active")
        else:
            base_qs = BankConnection.objects.filter(user=request.user, status="active")

        queryset = base_qs.select_related("institution", "session").prefetch_related("account_links__financial_account")
        if not force_all:
            queryset = queryset.filter(next_run_at__lte=now)

        payloads = []
        for connection in queryset:
            # If the user clicked "Sync now" recently, mark the lease as
            # manual so the run history surfaces it correctly. We treat
            # "next_run_at within the last 5 minutes of now" as a manual
            # nudge — automated reschedules land in the future.
            triggered_by = "scheduler"
            if connection.next_run_at is not None:
                lag = (now - connection.next_run_at).total_seconds()
                if 0 <= lag <= 300:
                    triggered_by = "manual"
            run = BankAutomationRun.objects.create(
                connection=connection,
                triggered_by=triggered_by,
            )
            payloads.append(self._serialize_runner_connection(connection, run))

        return Response({"connections": payloads, "now": now.isoformat()})


class RunnerRunOutcomeAPIView(_AuthMixin, APIView):
    """Internal endpoint: the runner records the outcome of a run.

    When the caller has ``is_automation_runner=True`` the run is looked up by
    ``pk`` only, allowing the runner to report outcomes for any user's run.
    Regular users are restricted to runs belonging to their own connections.
    """

    permission_classes = [IsAuthenticated | IsAutomationRunner]

    def post(self, request, run_id: int):
        if getattr(request.user, "is_automation_runner", False):
            run = BankAutomationRun.objects.filter(pk=run_id).select_related("connection").first()
        else:
            run = (
                BankAutomationRun.objects.filter(connection__user=request.user, pk=run_id)
                .select_related("connection")
                .first()
            )
        if run is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        succeeded = bool(request.data.get("succeeded"))
        failure_kind = str(request.data.get("failure_kind", "") or "")
        failure_reason = str(request.data.get("failure_reason", "") or "")
        accounts_attempted = int(request.data.get("accounts_attempted", 0) or 0)
        accounts_succeeded = int(request.data.get("accounts_succeeded", 0) or 0)
        statements_imported = int(request.data.get("statements_imported", 0) or 0)

        run.accounts_attempted = accounts_attempted
        run.accounts_succeeded = accounts_succeeded
        run.statements_imported = statements_imported
        if succeeded and accounts_succeeded > 0 and accounts_succeeded < accounts_attempted:
            run.status = "partial"
        run.save(
            update_fields=[
                "accounts_attempted",
                "accounts_succeeded",
                "statements_imported",
                "status",
            ]
        )

        record_run_outcome(
            run.connection,
            run,
            succeeded=succeeded,
            failure_kind=failure_kind,
            failure_reason=failure_reason,
        )

        run.refresh_from_db()
        run.connection.refresh_from_db()

        if succeeded:
            audit.audit(
                audit.EVENT_RUN_COMPLETED,
                user_id=run.connection.user_id,
                connection_id=run.connection.id,
                request=request,
                summary=f"imported={statements_imported}/{accounts_attempted}",
                metadata={"run_id": run.id},
            )
        else:
            audit.audit(
                audit.EVENT_RUN_FAILED,
                user_id=run.connection.user_id,
                connection_id=run.connection.id,
                request=request,
                summary=f"kind={failure_kind} attempted={accounts_attempted}",
                metadata={"run_id": run.id},
            )
            if failure_kind == "session_expired":
                audit.audit(
                    audit.EVENT_REAUTH_REQUIRED,
                    user_id=run.connection.user_id,
                    connection_id=run.connection.id,
                    request=request,
                )

        return Response(
            {
                "run": BankAutomationRunSerializer(run).data,
                "connection_status": run.connection.status,
                "next_run_at": run.connection.next_run_at.isoformat() if run.connection.next_run_at else None,
            }
        )
