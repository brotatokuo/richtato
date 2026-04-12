# Generated migration for expense_priority field

from django.db import migrations, models


def set_default_expense_priority(apps, schema_editor):
    """Set default expense_priority for existing expense categories."""
    TransactionCategory = apps.get_model("transaction", "TransactionCategory")
    TransactionCategory.objects.filter(type="expense").update(expense_priority="non_essential")


def reverse_expense_priority(apps, schema_editor):
    """Reverse: set all expense_priority to null."""
    TransactionCategory = apps.get_model("transaction", "TransactionCategory")
    TransactionCategory.objects.all().update(expense_priority=None)


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactioncategory",
            name="expense_priority",
            field=models.CharField(
                blank=True,
                choices=[
                    ("essential", "Essential"),
                    ("non_essential", "Non-Essential"),
                ],
                help_text="Only applies to expense categories. Essential = needs, Non-essential = wants",
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(set_default_expense_priority, reverse_expense_priority),
    ]
