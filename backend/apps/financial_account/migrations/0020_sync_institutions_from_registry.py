from django.db import migrations


def sync_institutions_from_registry(apps, schema_editor):
    FinancialInstitution = apps.get_model("financial_account", "FinancialInstitution")
    from apps.financial_account.institutions.registry import INSTITUTIONS

    for institution in INSTITUTIONS.values():
        FinancialInstitution.objects.update_or_create(
            slug=institution.slug,
            defaults={"name": institution.name},
        )

    registry_slugs = set(INSTITUTIONS.keys())
    orphan_qs = FinancialInstitution.objects.filter(accounts__isnull=True).exclude(slug__in=registry_slugs)

    # Legacy bank_sync rows still PROTECT institution FKs; skip those orphans.
    try:
        BankLogin = apps.get_model("bank_sync", "BankLogin")
    except LookupError:
        BankLogin = None
    if BankLogin is not None:
        protected_ids = set(
            BankLogin.objects.exclude(institution_id__isnull=True).values_list("institution_id", flat=True)
        )
        orphan_qs = orphan_qs.exclude(id__in=protected_ids)

    orphan_qs.delete()


def reverse_sync_institutions(apps, schema_editor):
    """No-op reverse: institution rows may already be referenced by accounts."""


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0019_add_investment_account_type"),
        ("bank_sync", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sync_institutions_from_registry, reverse_sync_institutions),
    ]
