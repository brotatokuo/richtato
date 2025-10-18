from datetime import date

from django.db import migrations


def migrate_category_budgets(apps, schema_editor):
    OldCategory = apps.get_model("richtato_user", "Category")
    Budget = apps.get_model("richtato_user", "Budget")

    # Use the historical model to avoid referencing fields that don't exist yet
    for category in OldCategory.objects.all():
        # Only migrate if the category had an old budget (e.g., pre-existing data)
        if hasattr(category, "budget"):
            Budget.objects.create(
                user=category.user,
                category=category,
                start_date=date(2020, 1, 1),  # Or whatever default range you want
                amount=category.budget,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("richtato_user", "0015_alter_category_options_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_category_budgets),
    ]
