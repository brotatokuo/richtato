# Migration to remove Category and CardAccount models from richtato_user app
# These models have been moved to apps.category and apps.card respectively

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("richtato_user", "0024_enhance_userpreference"),
        ("category", "0001_initial"),
        ("card", "0001_initial"),
    ]

    operations = [
        # We're not actually dropping the tables since they're still being used
        # by the new apps with db_table pointing to the same tables
        # This just removes them from Django's knowledge of the richtato_user app
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="category",
                    name="user",
                ),
                migrations.DeleteModel(
                    name="Category",
                ),
                migrations.RemoveField(
                    model_name="cardaccount",
                    name="user",
                ),
                migrations.DeleteModel(
                    name="CardAccount",
                ),
            ],
            database_operations=[
                # No database operations - tables remain as they are
            ],
        ),
    ]
