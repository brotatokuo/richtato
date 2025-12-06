"""Seed common financial institutions."""

from django.db import migrations


COMMON_INSTITUTIONS = [
    # Major US Banks
    {"name": "Chase", "slug": "chase"},
    {"name": "Bank of America", "slug": "bank_of_america"},
    {"name": "Wells Fargo", "slug": "wells_fargo"},
    {"name": "Citibank", "slug": "citibank"},
    {"name": "Capital One", "slug": "capital_one"},
    {"name": "US Bank", "slug": "us_bank"},
    {"name": "PNC Bank", "slug": "pnc"},
    {"name": "TD Bank", "slug": "td_bank"},
    # Online Banks
    {"name": "Ally Bank", "slug": "ally"},
    {"name": "Discover Bank", "slug": "discover"},
    {"name": "SoFi", "slug": "sofi"},
    # Credit Card Issuers
    {"name": "American Express", "slug": "american_express"},
    # Investment / Brokerage
    {"name": "Marcus by Goldman Sachs", "slug": "marcus"},
    {"name": "Robinhood", "slug": "robinhood"},
    {"name": "Charles Schwab", "slug": "schwab"},
    {"name": "Fidelity", "slug": "fidelity"},
    {"name": "Vanguard", "slug": "vanguard"},
    # Credit Unions
    {"name": "Navy Federal Credit Union", "slug": "navy_federal"},
    # Other
    {"name": "Other", "slug": "other"},
]


def seed_institutions(apps, schema_editor):
    """Create common financial institutions."""
    FinancialInstitution = apps.get_model("financial_account", "FinancialInstitution")

    for inst_data in COMMON_INSTITUTIONS:
        FinancialInstitution.objects.get_or_create(
            slug=inst_data["slug"], defaults={"name": inst_data["name"]}
        )


def reverse_seed(apps, schema_editor):
    """Remove seeded institutions (only if not linked to accounts)."""
    FinancialInstitution = apps.get_model("financial_account", "FinancialInstitution")

    slugs_to_remove = [inst["slug"] for inst in COMMON_INSTITUTIONS]
    # Only delete institutions that have no linked accounts
    FinancialInstitution.objects.filter(
        slug__in=slugs_to_remove, accounts__isnull=True
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("financial_account", "0003_add_is_liability_field"),
    ]

    operations = [
        migrations.RunPython(seed_institutions, reverse_seed),
    ]
