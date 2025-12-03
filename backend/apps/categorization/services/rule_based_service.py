"""Rule-based categorization service."""

from typing import Optional, Tuple

from apps.categorization.models import (
    CategorizationHistory,
    CategorizationRule,
    UserCategorizationPreference,
)
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from loguru import logger


class RuleBasedCategorizationService:
    """Service for rule-based transaction categorization."""

    def categorize_transaction(
        self, transaction: Transaction
    ) -> Optional[Tuple[TransactionCategory, CategorizationRule]]:
        """
        Attempt to categorize a transaction using user-defined rules.

        Args:
            transaction: Transaction to categorize

        Returns:
            Tuple of (category, rule) if a match is found, None otherwise
        """
        # Get active rules for this user, ordered by priority
        rules = CategorizationRule.objects.filter(
            user=transaction.user, is_active=True
        ).select_related("category")

        for rule in rules:
            if rule.matches(transaction):
                logger.info(
                    f"Rule match for transaction {transaction.id}: "
                    f"{rule.condition_type} = {rule.condition_value} → {rule.category.name}"
                )
                return (rule.category, rule)

        # Check user preferences (learned patterns)
        preference = self._check_user_preferences(transaction)
        if preference:
            logger.info(
                f"User preference match for transaction {transaction.id}: "
                f"{preference.description_pattern} → {preference.preferred_category.name}"
            )
            return (preference.preferred_category, None)

        return None

    def _check_user_preferences(
        self, transaction: Transaction
    ) -> Optional[UserCategorizationPreference]:
        """
        Check if user has a learned preference for this type of transaction.

        Args:
            transaction: Transaction to check

        Returns:
            UserCategorizationPreference if found, None otherwise
        """
        # First check by merchant if available
        if transaction.merchant:
            try:
                preference = UserCategorizationPreference.objects.get(
                    user=transaction.user, merchant=transaction.merchant
                )
                return preference
            except UserCategorizationPreference.DoesNotExist:
                pass

        # Then check by description pattern
        # Look for exact matches or similar patterns
        preferences = UserCategorizationPreference.objects.filter(
            user=transaction.user, merchant__isnull=True
        ).order_by("-use_count")

        for pref in preferences:
            if pref.description_pattern.lower() in transaction.description.lower():
                return pref

        return None

    def apply_categorization(
        self,
        transaction: Transaction,
        category: TransactionCategory,
        rule: Optional[CategorizationRule] = None,
    ) -> Transaction:
        """
        Apply a category to a transaction and record the history.

        Args:
            transaction: Transaction to categorize
            category: Category to apply
            rule: Optional rule that triggered the categorization

        Returns:
            Updated transaction
        """
        transaction.category = category
        transaction.save()

        # Record in history
        CategorizationHistory.objects.create(
            transaction=transaction,
            category=category,
            method="rule",
            rule=rule,
        )

        return transaction

    def create_rule(
        self,
        user: User,
        condition_type: str,
        condition_value: str,
        category: TransactionCategory,
        priority: int = 0,
        condition_value_max: str = "",
    ) -> CategorizationRule:
        """
        Create a new categorization rule.

        Args:
            user: Rule owner
            condition_type: Type of condition
            condition_value: Value to match
            category: Category to assign
            priority: Rule priority (higher = checked first)
            condition_value_max: Max value for range conditions

        Returns:
            Created rule
        """
        rule = CategorizationRule.objects.create(
            user=user,
            condition_type=condition_type,
            condition_value=condition_value,
            condition_value_max=condition_value_max,
            category=category,
            priority=priority,
        )

        logger.info(
            f"Created categorization rule for {user.username}: "
            f"{condition_type} = {condition_value} → {category.name}"
        )

        return rule

    def get_user_rules(self, user: User, active_only: bool = True):
        """Get all categorization rules for a user."""
        queryset = CategorizationRule.objects.filter(user=user).select_related(
            "category"
        )
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.all())

    def delete_rule(self, rule: CategorizationRule) -> None:
        """Delete a categorization rule."""
        rule.delete()
        logger.info(f"Deleted categorization rule {rule.id}")
