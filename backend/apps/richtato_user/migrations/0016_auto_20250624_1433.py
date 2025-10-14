from datetime import date

from django.db import migrations
from apps.richtato_user.models import Category


def migrate_category_budgets(apps, schema_editor):
    OldCategory = apps.get_model("richtato_user", "Category")
    Budget = apps.get_model("richtato_user", "Budget")

    for category in Category.objects.all():
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
