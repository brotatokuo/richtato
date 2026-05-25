"""Send daily bank-sync digest emails via Resend."""

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.core.services.email_service import EmailService
from apps.financial_account.services.sync_digest_service import SyncDigestService, default_since
from apps.richtato_user.models import User


class Command(BaseCommand):
    help = "Email daily bank-sync status digests to users with notifications enabled."

    def add_arguments(self, parser):
        parser.add_argument(
            "--since-hours",
            type=int,
            default=24,
            help="Look back this many hours for runs and statement imports (default: 24).",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send only to this user id (for testing).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print digest bodies without calling Resend.",
        )

    def handle(self, *args, **options):
        since_hours = options["since_hours"]
        since = default_since(hours=since_hours)
        service = SyncDigestService()

        users = self._eligible_users(options.get("user_id"))
        if not users:
            self.stdout.write(self.style.WARNING("No eligible users to notify."))
            return

        sent = 0
        skipped = 0
        failed = 0

        for user in users:
            digest = service.build_digest_for_user(user, since=since)
            if options["dry_run"]:
                self.stdout.write(self.style.SUCCESS(f"--- {user.username} <{user.email}> ---"))
                self.stdout.write(f"Subject: {digest.subject}")
                self.stdout.write(digest.to_text())
                self.stdout.write("")
                continue

            if not EmailService.is_configured():
                self.stderr.write(
                    self.style.ERROR(
                        "RESEND_API_KEY and RESEND_FROM_EMAIL must be set to send emails. "
                        "Use --dry-run to preview without sending."
                    )
                )
                return

            ok = EmailService.send(
                to=user.email,
                subject=digest.subject,
                text=digest.to_text(),
                html=digest.to_html(),
            )
            if ok:
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"Sent digest to {user.email}"))
            else:
                failed += 1
                self.stderr.write(self.style.ERROR(f"Failed to send digest to {user.email}"))

        if not options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(f"Done: sent={sent} failed={failed} skipped={skipped} users={len(users)}")
            )

    def _eligible_users(self, user_id: int | None) -> list[User]:
        qs = User.objects.filter(is_active=True).exclude(Q(email__isnull=True) | Q(email=""))
        if user_id is not None:
            qs = qs.filter(id=user_id)

        eligible: list[User] = []
        for user in qs.select_related("preferences"):
            pref = getattr(user, "preferences", None)
            if pref is not None and not pref.notifications_enabled:
                continue
            if pref is not None and not pref.bank_sync_daily_digest:
                continue
            eligible.append(user)
        return eligible
