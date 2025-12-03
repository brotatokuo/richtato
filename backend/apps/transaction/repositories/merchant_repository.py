"""Repository for Merchant model."""

from typing import List, Optional

from apps.transaction.models import Merchant, TransactionCategory


class MerchantRepository:
    """Repository for merchant data access."""

    def get_by_id(self, merchant_id: int) -> Optional[Merchant]:
        """Get merchant by ID."""
        try:
            return Merchant.objects.get(id=merchant_id)
        except Merchant.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[Merchant]:
        """Get merchant by slug."""
        try:
            return Merchant.objects.get(slug=slug)
        except Merchant.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Optional[Merchant]:
        """Get merchant by name."""
        try:
            return Merchant.objects.get(name__iexact=name)
        except Merchant.DoesNotExist:
            return None

    def get_all(self) -> List[Merchant]:
        """Get all merchants."""
        return list(Merchant.objects.all())

    def create_merchant(
        self,
        name: str,
        slug: str,
        category_hint: TransactionCategory = None,
        logo_url: str = None,
    ) -> Merchant:
        """Create a new merchant."""
        return Merchant.objects.create(
            name=name, slug=slug, category_hint=category_hint, logo_url=logo_url
        )

    def get_or_create_merchant(self, name: str, slug: str = None, **kwargs) -> Merchant:
        """Get or create a merchant."""
        if slug is None:
            slug = name.lower().replace(" ", "_")
        merchant, created = Merchant.objects.get_or_create(
            slug=slug, defaults={"name": name, **kwargs}
        )
        return merchant

    def update_merchant(self, merchant: Merchant, **kwargs) -> Merchant:
        """Update merchant fields."""
        for key, value in kwargs.items():
            if hasattr(merchant, key):
                setattr(merchant, key, value)
        merchant.save()
        return merchant
