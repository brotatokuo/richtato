"""
Management command to delete a user and all their data.

Usage:
    python manage.py delete_user_data --username tepolak
    python manage.py delete_user_data --user-id 5
    python manage.py delete_user_data --username tepolak --keep-user
    python manage.py delete_user_data --username tepolak --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_delete, post_save

from apps.budget.models import Budget
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.signals import transaction_post_delete, transaction_post_save


class Command(BaseCommand):
    help = "Delete a user and all their associated data"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--username",
            type=str,
            help="Username of the user to delete",
        )
        group.add_argument(
            "--user-id",
            type=int,
            help="ID of the user to delete",
        )
        parser.add_argument(
            "--keep-user",
            action="store_true",
            help="Keep the user account, only delete their data",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        user_id = options.get("user_id")
        keep_user = options.get("keep_user")
        force = options.get("force")

        # Find user
        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f"User not found: {username or f'ID {user_id}'}")

        # Count data to be deleted
        counts = self._count_user_data(user)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"User: {user.username} (ID: {user.id})")
        self.stdout.write("=" * 50)
        self.stdout.write("\nData to be deleted:")
        self.stdout.write(f"  - Transactions: {counts['transactions']}")
        self.stdout.write(f"  - Balance History: {counts['balance_history']}")
        self.stdout.write(f"  - Financial Accounts: {counts['accounts']}")
        self.stdout.write(f"  - Categories: {counts['categories']}")
        self.stdout.write(f"  - Budgets: {counts['budgets']}")
        self.stdout.write(f"  - Budget Allocations: {counts['budget_allocations']}")

        if not keep_user:
            self.stdout.write(self.style.WARNING("\n⚠️  The user account will also be deleted!"))
        else:
            self.stdout.write("\n  User account will be kept.")

        total = sum(counts.values())
        if total == 0 and keep_user:
            self.stdout.write(self.style.WARNING("\nNo data to delete."))
            return

        # Confirm deletion
        if not force:
            self.stdout.write("")
            confirm = input("Are you sure you want to delete this data? [yes/no]: ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        # Delete data
        with transaction.atomic():
            deleted = self._delete_user_data(user, keep_user)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Deletion complete!"))
        self.stdout.write(f"  - Transactions deleted: {deleted['transactions']}")
        self.stdout.write(f"  - Balance History deleted: {deleted['balance_history']}")
        self.stdout.write(f"  - Financial Accounts deleted: {deleted['accounts']}")
        self.stdout.write(f"  - Categories deleted: {deleted['categories']}")
        self.stdout.write(f"  - Budgets deleted: {deleted['budgets']}")
        if not keep_user:
            self.stdout.write(f"  - User deleted: {user.username}")

    def _count_user_data(self, user):
        """Count all data associated with a user."""
        accounts = FinancialAccount.objects.filter(user=user)
        account_ids = list(accounts.values_list("id", flat=True))

        return {
            "transactions": Transaction.objects.filter(user=user).count(),
            "balance_history": AccountBalanceHistory.objects.filter(account_id__in=account_ids).count(),
            "accounts": accounts.count(),
            "categories": TransactionCategory.objects.filter(user=user).count(),
            "budgets": Budget.objects.filter(user=user).count(),
            "budget_allocations": sum(b.budget_categories.count() for b in Budget.objects.filter(user=user)),
        }

    def _delete_user_data(self, user, keep_user=False):
        """Delete all data associated with a user."""
        deleted = {}

        # Disconnect signals to avoid errors when deleting transactions
        # (the post_delete signal tries to access the account which may be deleted)
        post_save.disconnect(transaction_post_save, sender=Transaction)
        post_delete.disconnect(transaction_post_delete, sender=Transaction)

        try:
            # Delete transactions first (has FK to accounts and categories)
            deleted["transactions"] = Transaction.objects.filter(user=user).delete()[0]

            # Get account IDs before deleting
            accounts = FinancialAccount.objects.filter(user=user)
            account_ids = list(accounts.values_list("id", flat=True))

            # Delete balance history (FK to accounts)
            deleted["balance_history"] = AccountBalanceHistory.objects.filter(account_id__in=account_ids).delete()[0]

            # Delete accounts
            deleted["accounts"] = accounts.delete()[0]

            # Delete categories
            deleted["categories"] = TransactionCategory.objects.filter(user=user).delete()[0]

            # Delete budgets (cascade deletes budget allocations)
            deleted["budgets"] = Budget.objects.filter(user=user).delete()[0]

            # Delete user if requested
            if not keep_user:
                user.delete()

            return deleted
        finally:
            # Re-enable signals
            post_save.connect(transaction_post_save, sender=Transaction)
            post_delete.connect(transaction_post_delete, sender=Transaction)
