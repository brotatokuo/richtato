from datetime import date

from django.db import migrations


def migrate_category_budgets(apps, schema_editor):
    OldCategory = apps.get_model("richtato_user", "Category")
    Budget = apps.get_model("richtato_user", "Budget")

    # Use the historical model state provided by `apps` to avoid referencing
    # fields that may not exist yet (e.g., `enabled`) on the live model.
    for category in OldCategory.objects.all():
        # If the historical Category still had a `budget` field at this point,
        # migrate it into the new Budget model. If not present, skip.
        if hasattr(category, "budget"):
            Budget.objects.create(
                user=category.user,
                category=category,
                start_date=date(2020, 1, 1),
                amount=category.budget,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("richtato_user", "0015_alter_category_options_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_category_budgets),
    ]
