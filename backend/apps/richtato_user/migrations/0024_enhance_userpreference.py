# Migration to add new fields to UserPreference

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("richtato_user", "0023_userpreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="language",
            field=models.CharField(
                default="en", help_text="User interface language", max_length=5
            ),
        ),
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
        migrations.AlterField(
            model_name="userpreference",
            name="theme",
            field=models.CharField(
                default="system", help_text="UI theme preference", max_length=10
            ),
        ),
        migrations.AlterField(
            model_name="userpreference",
            name="currency",
            field=models.CharField(
                default="USD",
                help_text="Preferred currency code (e.g., USD, EUR, GBP)",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="userpreference",
            name="date_format",
            field=models.CharField(
                default="MM/DD/YYYY",
                help_text="Preferred date display format",
                max_length=20,
            ),
        ),
        migrations.AlterModelOptions(
            name="userpreference",
            options={"verbose_name_plural": "User Preferences"},
        ),
    ]
