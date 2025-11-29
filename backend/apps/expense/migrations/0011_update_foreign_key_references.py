# Migration to update ForeignKey references after moving Category and CardAccount models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("expense", "0010_set_negative_amounts"),
        ("richtato_user", "0025_remove_category_cardaccount"),
        ("category", "0001_initial"),
        ("card", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update references to point to new app locations
        # No database changes needed since db_table points to same tables
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="expense",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="expenses",
                        to="category.category",
                    ),
                ),
                migrations.AlterField(
                    model_name="expense",
                    name="account_name",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="expenses",
                        to="card.cardaccount",
                    ),
                ),
            ],
            database_operations=[
                # No database operations - just updating Django's state
            ],
        ),
    ]
