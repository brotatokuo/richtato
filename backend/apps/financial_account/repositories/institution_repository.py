"""Repository for FinancialInstitution model."""

from typing import List, Optional

from apps.financial_account.models import FinancialInstitution


class FinancialInstitutionRepository:
    """Repository for financial institution data access."""

    def get_by_id(self, institution_id: int) -> Optional[FinancialInstitution]:
        """Get institution by ID."""
        try:
            return FinancialInstitution.objects.get(id=institution_id)
        except FinancialInstitution.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> Optional[FinancialInstitution]:
        """Get institution by slug."""
        try:
            return FinancialInstitution.objects.get(slug=slug)
        except FinancialInstitution.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Optional[FinancialInstitution]:
        """Get institution by name."""
        try:
            return FinancialInstitution.objects.get(name__iexact=name)
        except FinancialInstitution.DoesNotExist:
            return None

    def get_all(self) -> List[FinancialInstitution]:
        """Get all institutions."""
        return list(FinancialInstitution.objects.all())

    def create_institution(
        self,
        name: str,
        slug: str,
        logo_url: Optional[str] = None,
        support_url: Optional[str] = None,
    ) -> FinancialInstitution:
        """Create a new financial institution."""
        return FinancialInstitution.objects.create(
            name=name, slug=slug, logo_url=logo_url, support_url=support_url
        )

    def get_or_create_institution(
        self, name: str, slug: Optional[str] = None, **kwargs
    ) -> FinancialInstitution:
        """Get or create an institution by name (which has unique constraint)."""
        if slug is None:
            slug = name.lower().replace(" ", "_").replace("-", "_")

        institution, created = FinancialInstitution.objects.get_or_create(
            name=name, defaults={"slug": slug, **kwargs}
        )
        return institution
