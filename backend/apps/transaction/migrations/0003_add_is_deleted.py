# Generated migration for is_deleted field on TransactionCategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transaction", "0002_add_expense_priority"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactioncategory",
            name="is_deleted",
            field=models.BooleanField(
                default=False,
                help_text="Soft delete - hidden from UI but preserves transaction assignments",
            ),
        ),
    ]
