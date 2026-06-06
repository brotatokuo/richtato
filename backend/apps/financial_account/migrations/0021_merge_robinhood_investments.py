from django.db import migrations


def merge_robinhood_investments(apps, schema_editor):
    FinancialInstitution = apps.get_model("financial_account", "FinancialInstitution")
    FinancialAccount = apps.get_model("financial_account", "FinancialAccount")

    robinhood, _ = FinancialInstitution.objects.get_or_create(
        slug="robinhood",
        defaults={"name": "Robinhood"},
    )
    legacy = FinancialInstitution.objects.filter(slug="robinhood_investments").first()
    if legacy is None:
        return

    FinancialAccount.objects.filter(institution=legacy).update(institution=robinhood)
    if not FinancialAccount.objects.filter(institution=legacy).exists():
        legacy.delete()


def reverse_merge_robinhood_investments(apps, schema_editor):
    """No-op reverse: accounts remain under Robinhood."""


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0020_sync_institutions_from_registry"),
    ]

    operations = [
        migrations.RunPython(merge_robinhood_investments, reverse_merge_robinhood_investments),
    ]
