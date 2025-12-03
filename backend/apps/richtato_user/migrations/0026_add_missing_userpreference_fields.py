# Migration to add missing fields that weren't in the database

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("richtato_user", "0025_remove_category_cardaccount"),
    ]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="timezone",
            field=models.CharField(
                default="UTC",
                help_text="User timezone (e.g., America/New_York, Europe/London)",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="userpreference",
            name="notifications_enabled",
            field=models.BooleanField(
                default=True, help_text="Whether to receive notifications"
            ),
        ),
    ]
