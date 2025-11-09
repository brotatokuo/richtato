from django.db import migrations
from django.db.models import F


def set_negative_amounts(apps, schema_editor):
    Expense = apps.get_model("expense", "Expense")
    # For any existing expense with a positive amount, make it negative
    Expense.objects.filter(amount__gt=0).update(amount=F("amount") * -1)


def revert_negative_amounts(apps, schema_editor):
    Expense = apps.get_model("expense", "Expense")
    # Revert: for any existing expense with a negative amount, make it positive
    Expense.objects.filter(amount__lt=0).update(amount=F("amount") * -1)


class Migration(migrations.Migration):
    dependencies = [
        ("expense", "0009_alter_expense_category"),
    ]

    operations = [
        migrations.RunPython(set_negative_amounts, revert_negative_amounts),
    ]
