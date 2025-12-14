# Generated migration for categorization redesign

import django.db.models.deletion
from django.db import migrations, models


def migrate_category_types(apps, schema_editor):
    """Migrate is_income/is_expense to type field."""
    TransactionCategory = apps.get_model("transaction", "TransactionCategory")

    # Update all categories based on their is_income/is_expense flags
    for category in TransactionCategory.objects.all():
        if category.is_income:
            category.type = "income"
        elif category.is_expense:
            category.type = "expense"
        else:
            # Default to expense if neither flag is set
            category.type = "expense"
        category.save(update_fields=["type"])


def reverse_category_types(apps, schema_editor):
    """Reverse migration - restore is_income/is_expense from type."""
    TransactionCategory = apps.get_model("transaction", "TransactionCategory")

    for category in TransactionCategory.objects.all():
        if category.type == "income":
            category.is_income = True
            category.is_expense = False
        elif category.type == "expense":
            category.is_income = False
            category.is_expense = True
        else:  # transfer
            category.is_income = False
            category.is_expense = False
        category.save(update_fields=["is_income", "is_expense"])


class Migration(migrations.Migration):

    dependencies = [
        ("transaction", "0002_transaction_notes_keywordrule"),
    ]

    operations = [
        # Add type field to TransactionCategory
        migrations.AddField(
            model_name="transactioncategory",
            name="type",
            field=models.CharField(
                choices=[
                    ("income", "Income"),
                    ("expense", "Expense"),
                    ("transfer", "Transfer"),
                ],
                default="expense",
                help_text="Category type determines transaction classification",
                max_length=20,
            ),
        ),
        # Add index for type field
        migrations.AddIndex(
            model_name="transactioncategory",
            index=models.Index(fields=["type"], name="transaction_type_idx"),
        ),
        # Migrate data from is_income/is_expense to type
        migrations.RunPython(migrate_category_types, reverse_category_types),
        # Create CategoryKeyword model
        migrations.CreateModel(
            name="CategoryKeyword",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "keyword",
                    models.CharField(
                        help_text="Case-insensitive keyword for matching",
                        max_length=200,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "match_count",
                    models.IntegerField(
                        default=0, help_text="Number of times this keyword has matched"
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="keywords",
                        to="transaction.transactioncategory",
                    ),
                ),
            ],
            options={
                "db_table": "category_keyword",
                "ordering": ["-match_count", "keyword"],
            },
        ),
        # Add indexes for CategoryKeyword
        migrations.AddIndex(
            model_name="categorykeyword",
            index=models.Index(fields=["keyword"], name="category_kw_keyword_idx"),
        ),
        migrations.AddIndex(
            model_name="categorykeyword",
            index=models.Index(fields=["category"], name="category_kw_category_idx"),
        ),
        # Add unique constraint
        migrations.AlterUniqueTogether(
            name="categorykeyword",
            unique_together={("category", "keyword")},
        ),
    ]
