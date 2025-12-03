"""Learning service for improving categorization based on user corrections."""

from typing import Optional

from apps.categorization.models import UserCategorizationPreference
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from django.db.models import F
from loguru import logger


class LearningService:
    """Service for learning from user categorization corrections."""

    def record_user_choice(
        self, user: User, transaction: Transaction, category: TransactionCategory
    ) -> UserCategorizationPreference:
        """
        Record a user's manual categorization choice to improve future suggestions.

        Args:
            user: User who made the choice
            transaction: Transaction that was categorized
            category: Category chosen by user

        Returns:
            Updated or created preference
        """
        # Extract pattern from description (first 3 words or merchant name)
        description_pattern = self._extract_pattern(transaction.description)

        # Check if preference already exists
        try:
            if transaction.merchant:
                # Merchant-based preference
                preference = UserCategorizationPreference.objects.get(
                    user=user,
                    merchant=transaction.merchant,
                    description_pattern=description_pattern,
                )
            else:
                # Description-based preference
                preference = UserCategorizationPreference.objects.get(
                    user=user,
                    merchant__isnull=True,
                    description_pattern=description_pattern,
                )

            # Update existing preference
            preference.preferred_category = category
            preference.use_count = F("use_count") + 1
            preference.save()
            preference.refresh_from_db()

            logger.info(
                f"Updated user preference for {user.username}: "
                f"{description_pattern} → {category.name} (count: {preference.use_count})"
            )

        except UserCategorizationPreference.DoesNotExist:
            # Create new preference
            preference = UserCategorizationPreference.objects.create(
                user=user,
                description_pattern=description_pattern,
                merchant=transaction.merchant,
                preferred_category=category,
                use_count=1,
            )

            logger.info(
                f"Created user preference for {user.username}: "
                f"{description_pattern} → {category.name}"
            )

        return preference

    def _extract_pattern(self, description: str) -> str:
        """
        Extract a meaningful pattern from transaction description.

        Args:
            description: Transaction description

        Returns:
            Extracted pattern (normalized)
        """
        # Clean and normalize
        pattern = description.strip().lower()

        # Take first 50 characters or first 3 words
        words = pattern.split()
        if len(words) > 3:
            pattern = " ".join(words[:3])
        else:
            pattern = pattern[:50]

        return pattern

    def get_suggested_category(
        self, user: User, transaction: Transaction
    ) -> Optional[TransactionCategory]:
        """
        Get a suggested category based on learned preferences.

        Args:
            user: User
            transaction: Transaction to categorize

        Returns:
            Suggested category if found, None otherwise
        """
        # First check by merchant
        if transaction.merchant:
            try:
                preference = (
                    UserCategorizationPreference.objects.filter(
                        user=user, merchant=transaction.merchant
                    )
                    .order_by("-use_count")
                    .first()
                )
                if preference:
                    return preference.preferred_category
            except:
                pass

        # Then check by description pattern
        description_pattern = self._extract_pattern(transaction.description)
        preference = (
            UserCategorizationPreference.objects.filter(
                user=user,
                description_pattern__icontains=description_pattern,
            )
            .order_by("-use_count")
            .first()
        )

        if preference:
            return preference.preferred_category

        return None

    def get_user_preferences(self, user: User, limit: int = 100):
        """Get user's categorization preferences."""
        return list(
            UserCategorizationPreference.objects.filter(user=user)
            .select_related("merchant", "preferred_category")
            .order_by("-use_count", "-last_used")[:limit]
        )
