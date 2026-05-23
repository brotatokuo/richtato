"""Views for the bank sync API.

End-user endpoints use Session/Token auth and only ever return the user's
own ``BankLogin`` rows. Agent endpoints under ``runner/`` use Token auth
with the ``automation_runner`` service account and span all users.
"""

from __future__ import annotations

from django.db import transaction
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

from apps.bank_sync import audit
from apps.bank_sync.models import BankLogin, SyncedAccount, SyncRun
from apps.bank_sync.serializers import (
    BankLoginCreateSerializer,
    BankLoginSerializer,
    BankLoginUpdateSerializer,
    CapturedSessionSerializer,
    RunOutcomeSerializer,
    SyncedAccountBulkBindSerializer,
    SyncedAccountSerializer,
    SyncedAccountUpdateSerializer,
    SyncRunSerializer,
)
from apps.bank_sync.services import login_service, run_service, session_service
from apps.bank_sync.services.scheduling import reschedule
from apps.financial_account.models import FinancialAccount, FinancialInstitution

# Slugs of institutions for which a Playwright adapter exists today. Keep in
# sync with scripts/bank_sync/institutions/.
SUPPORTED_ADAPTER_SLUGS = ("bofa", "chase")


class _ManualSyncThrottle(UserRateThrottle):
    """Throttle the manual 'Sync now' / 'Begin login' endpoints to be kind to banks."""

    scope = "bank_sync_manual"

    def get_rate(self):
        return "30/hour"


class IsAutomationRunner(BasePermission):
    """Grants access only to accounts with ``is_automation_runner=True``."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and getattr(request.user, "is_automation_runner", False)
        )


class _AuthMixin:
    """Session + Token + Basic auth for end-user endpoints."""

    authentication_classes = [
        SessionAuthentication,
        TokenAuthentication,
        BasicAuthentication,
    ]
    permission_classes = [IsAuthenticated]


class BankLoginListAPIView(_AuthMixin, APIView):
    """List or create the user's bank logins."""

    def get(self, request):
        logins = (
            BankLogin.objects.filter(user=request.user)
            .select_related("institution")
            .prefetch_related("synced_accounts__financial_account")
        )
        serializer = BankLoginSerializer(logins, many=True)
        return Response({"logins": serializer.data})

    def post(self, request):
        serializer = BankLoginCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        institution = FinancialInstitution.objects.filter(id=data["institution"]).first()
        if institution is None:
            return Response(
                {"error": "Institution not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not any(_institution_matches_slug(institution.slug, supported) for supported in SUPPORTED_ADAPTER_SLUGS):
            return Response(
                {"error": f"Institution {institution.slug!r} is not supported by the Playwright agent"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login = login_service.create_login(
            user=request.user,
            institution=institution,
            nickname=data.get("nickname", ""),
            cadence=data.get("cadence", "daily"),
            preferred_run_hour_local=data.get("preferred_run_hour_local", 6),
        )
        audit.audit(
            audit.EVENT_LOGIN_CREATED,
            user_id=request.user.id,
            login_id=login.id,
            request=request,
            summary=f"institution={institution.slug}",
        )
        return Response(
            BankLoginSerializer(login).data,
            status=status.HTTP_201_CREATED,
        )


class BankLoginDetailAPIView(_AuthMixin, APIView):
    """Retrieve / update / delete a single bank login."""

    def _get(self, request, pk):
        return (
            BankLogin.objects.filter(user=request.user, pk=pk)
            .select_related("institution")
            .prefetch_related("synced_accounts__financial_account")
            .first()
        )

    def get(self, request, pk):
        login = self._get(request, pk)
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BankLoginSerializer(login).data)

    def patch(self, request, pk):
        login = self._get(request, pk)
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BankLoginUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        login_service.update_login(login, **serializer.validated_data)
        login.refresh_from_db()
        audit.audit(
            audit.EVENT_LOGIN_UPDATED,
            user_id=request.user.id,
            login_id=login.id,
            request=request,
            summary=f"cadence={login.cadence} hour={login.preferred_run_hour_local}",
        )
        return Response(BankLoginSerializer(login).data)

    def delete(self, request, pk):
        login = self._get(request, pk)
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        login_id = login.id
        login.delete()
        audit.audit(
            audit.EVENT_LOGIN_DELETED,
            user_id=request.user.id,
            login_id=login_id,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class BankLoginBeginLoginAPIView(_AuthMixin, APIView):
    """Queue an ``interactive_login`` task so the agent pops a headed browser."""

    throttle_classes = [_ManualSyncThrottle]

    def post(self, request, pk):
        login = BankLogin.objects.filter(user=request.user, pk=pk).first()
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if login.status == "disabled":
            return Response(
                {"error": "Login is disabled; reactivate it first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        run = run_service.queue_interactive_login(login, triggered_by="user_login")
        audit.audit(
            audit.EVENT_INTERACTIVE_LOGIN_STARTED,
            user_id=request.user.id,
            login_id=login.id,
            request=request,
            metadata={"run_id": run.id},
        )
        return Response(
            {"run_id": run.id, "status": run.status, "queued_at": run.queued_at.isoformat()},
            status=status.HTTP_202_ACCEPTED,
        )


class BankLoginSyncNowAPIView(_AuthMixin, APIView):
    """Queue an immediate ``scheduled_download`` for this login."""

    throttle_classes = [_ManualSyncThrottle]

    def post(self, request, pk):
        login = BankLogin.objects.filter(user=request.user, pk=pk).first()
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if login.status != "active":
            return Response(
                {
                    "error": f"Login is {login.status}; sign in first.",
                    "status": login.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        run = run_service.queue_manual_download(login)
        audit.audit(
            audit.EVENT_MANUAL_SYNC_REQUESTED,
            user_id=request.user.id,
            login_id=login.id,
            request=request,
            metadata={"run_id": run.id},
        )
        return Response(
            {"run_id": run.id, "queued_at": run.queued_at.isoformat()},
            status=status.HTTP_202_ACCEPTED,
        )


class BankLoginDisableAPIView(_AuthMixin, APIView):
    """Pause automation without deleting the stored cookies."""

    def post(self, request, pk):
        login = BankLogin.objects.filter(user=request.user, pk=pk).first()
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        login_service.disable_login(login)
        audit.audit(
            audit.EVENT_LOGIN_UPDATED,
            user_id=request.user.id,
            login_id=login.id,
            request=request,
            summary="disabled",
        )
        return Response(BankLoginSerializer(login).data)


class BankLoginRunsAPIView(_AuthMixin, APIView):
    """Run history for a bank login."""

    def get(self, request, pk):
        login = BankLogin.objects.filter(user=request.user, pk=pk).first()
        if login is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        runs = login.runs.all()[:50]
        return Response({"runs": SyncRunSerializer(runs, many=True).data})


class SyncedAccountListAPIView(_AuthMixin, APIView):
    """List the user's synced accounts."""

    def get(self, request):
        accounts = (
            SyncedAccount.objects.filter(bank_login__user=request.user)
            .select_related("bank_login__institution", "financial_account")
            .order_by("bank_login_id", "id")
        )
        return Response({"accounts": SyncedAccountSerializer(accounts, many=True).data})


class SyncedAccountDetailAPIView(_AuthMixin, APIView):
    """PATCH or DELETE a single synced account."""

    def patch(self, request, pk):
        account = SyncedAccount.objects.filter(bank_login__user=request.user, pk=pk).first()
        if account is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SyncedAccountUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        for field in ("enabled", "flow"):
            if field in data:
                setattr(account, field, data[field])
        account.save()
        return Response(SyncedAccountSerializer(account).data)

    def delete(self, request, pk):
        account = SyncedAccount.objects.filter(bank_login__user=request.user, pk=pk).first()
        if account is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        login_service.unbind_account(account)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SyncedAccountBulkBindAPIView(_AuthMixin, APIView):
    """Wizard step 3: confirm/bind detected bank accounts to Richtato accounts."""

    def post(self, request):
        serializer = SyncedAccountBulkBindSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bound = []
        for row in serializer.validated_data["accounts"]:
            login = BankLogin.objects.filter(user=request.user, pk=row["bank_login"]).first()
            if login is None:
                return Response(
                    {"error": f"BankLogin {row['bank_login']} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fa = FinancialAccount.objects.filter(user=request.user, pk=row["financial_account"]).first()
            if fa is None:
                return Response(
                    {"error": f"FinancialAccount {row['financial_account']} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            synced = login_service.bind_account(
                bank_login=login,
                financial_account=fa,
                flow=row["flow"],
                external_account_token=row.get("external_account_token", ""),
                activity_url=row.get("activity_url", ""),
                detected_account_name=row.get("detected_account_name", ""),
            )
            bound.append(synced)
        return Response(
            {"accounts": SyncedAccountSerializer(bound, many=True).data},
            status=status.HTTP_201_CREATED,
        )


class SupportedInstitutionsAPIView(_AuthMixin, APIView):
    """List the institutions the agent can drive today."""

    def get(self, request):
        institutions = []
        deposit_capable = {"bofa", "chase"}
        credit_capable = {"bofa", "chase"}
        for slug in SUPPORTED_ADAPTER_SLUGS:
            inst = FinancialInstitution.objects.filter(slug=slug).first()
            institutions.append(
                {
                    "slug": slug,
                    "name": inst.name if inst else slug.title(),
                    "id": inst.id if inst else None,
                    "supports_deposit": slug in deposit_capable,
                    "supports_credit_card": slug in credit_capable,
                }
            )
        return Response({"institutions": institutions})


class BindableAccountsAPIView(_AuthMixin, APIView):
    """List Richtato accounts a user can bind to a discovered bank account."""

    def get(self, request):
        slug = (request.query_params.get("institution_slug") or "").strip().lower()
        accounts_qs = (
            FinancialAccount.objects.filter(user=request.user, is_active=True)
            .select_related("institution")
            .order_by("name")
        )
        existing_bindings = set(
            SyncedAccount.objects.filter(bank_login__user=request.user).values_list("financial_account_id", flat=True)
        )
        accounts = []
        for account in accounts_qs:
            inst_slug = account.institution.slug if account.institution_id else ""
            matches = bool(slug) and (inst_slug == slug or _institution_matches_slug(inst_slug, slug))
            flow = "credit_card" if account.account_type == "credit_card" else "deposit"
            accounts.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "account_type_display": account.get_account_type_display(),
                    "account_number_last4": account.account_number_last4 or "",
                    "institution_slug": inst_slug,
                    "institution_name": account.institution.name if account.institution_id else "",
                    "flow": flow,
                    "matches_institution": matches,
                    "already_bound": account.id in existing_bindings,
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


# Slug aliases so the bofa adapter's "bofa" lookup matches the
# seeded "bank_of_america" institution row and similar variants. Anything
# else uses strict equality.
_SLUG_ALIASES: dict[str, set[str]] = {
    "bofa": {"bofa", "bank_of_america", "bankofamerica"},
    "chase": {"chase", "jpmorgan_chase", "jpmc"},
}


def _institution_matches_slug(account_slug: str, agent_slug: str) -> bool:
    aliases = _SLUG_ALIASES.get(agent_slug, {agent_slug})
    return account_slug in aliases


class _RunnerAuthMixin:
    """Token-auth only for agent endpoints."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAutomationRunner]


class RunnerDueTasksAPIView(_RunnerAuthMixin, APIView):
    """Agent fetches queued + due tasks and marks them ``running``."""

    def get(self, request):
        kinds_raw = (request.query_params.get("task_kinds") or "").strip()
        task_kinds = None
        if kinds_raw:
            task_kinds = tuple(k.strip() for k in kinds_raw.split(",") if k.strip())
        leased = run_service.lease_due_tasks(task_kinds=task_kinds)
        payloads = []
        for run in leased:
            payloads.append(session_service.serialize_runner_task(run))
        return Response({"tasks": payloads, "now": timezone.now().isoformat()})


class RunnerCapturedSessionAPIView(_RunnerAuthMixin, APIView):
    """Agent reports a successful interactive_login: storage_state + discovered accounts."""

    def post(self, request, run_id: int):
        run = SyncRun.objects.filter(pk=run_id).select_related("bank_login").first()
        if run is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CapturedSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        with transaction.atomic():
            login = run.bank_login
            session_service.store_storage_state(login, data["storage_state"])
            discovered = list(data.get("discovered_accounts") or [])
            login_service.activate_after_capture(login)
        audit.audit(
            audit.EVENT_SESSION_CAPTURED,
            user_id=login.user_id,
            login_id=login.id,
            request=request,
            summary=f"discovered={len(discovered)}",
            metadata={"run_id": run.id},
        )
        return Response(
            {
                "login": BankLoginSerializer(login).data,
                "discovered_accounts": discovered,
            }
        )


class RunnerRunOutcomeAPIView(_RunnerAuthMixin, APIView):
    """Agent reports completion (success or failure) of a SyncRun."""

    def post(self, request, run_id: int):
        run = SyncRun.objects.filter(pk=run_id).select_related("bank_login").first()
        if run is None:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = RunOutcomeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        run_service.record_outcome(
            run,
            succeeded=data["succeeded"],
            failure_kind=data.get("failure_kind", ""),
            failure_reason=data.get("failure_reason", ""),
            accounts_attempted=data.get("accounts_attempted", 0),
            accounts_succeeded=data.get("accounts_succeeded", 0),
            statements_imported=data.get("statements_imported", 0),
        )
        login = run.bank_login
        login.refresh_from_db()
        if data["succeeded"]:
            audit.audit(
                audit.EVENT_SYNC_SUCCEEDED,
                user_id=login.user_id,
                login_id=login.id,
                request=request,
                summary=f"imported={data.get('statements_imported', 0)}",
                metadata={"run_id": run.id, "task_kind": run.task_kind},
            )
        else:
            audit.audit(
                audit.EVENT_SYNC_FAILED,
                user_id=login.user_id,
                login_id=login.id,
                request=request,
                summary=f"kind={data.get('failure_kind', '')}",
                metadata={"run_id": run.id, "task_kind": run.task_kind},
            )
            if data.get("failure_kind") == "needs_reauth":
                audit.audit(
                    audit.EVENT_REAUTH_REQUIRED,
                    user_id=login.user_id,
                    login_id=login.id,
                    request=request,
                )
        return Response(
            {
                "run": SyncRunSerializer(run).data,
                "login_status": login.status,
                "next_run_at": login.next_run_at.isoformat() if login.next_run_at else None,
            }
        )


# Touch the imports so unused-import lints don't fire while we're early in
# the rollout. Some helpers (reschedule, logger) are exported for future
# views or tests.
_ = (reschedule, logger)
