# Migration to update Category ForeignKey reference after moving Category model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("budget", "0001_initial"),
        ("richtato_user", "0025_remove_category_cardaccount"),
        ("category", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update category reference to point to new app location
        # No database changes needed since db_table points to same table
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="budget",
                    name="category",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="budgets",
                        to="category.category",
                    ),
                ),
            ],
            database_operations=[
                # No database operations - just updating Django's state
            ],
        ),
    ]
