from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0021_merge_robinhood_investments"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialaccount",
            name="agent_cadence",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("monthly", "Monthly"),
                ],
                default="daily",
                help_text="Host bank-agent sync cadence when sync_mode is auto.",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="financialaccount",
            name="agent_sync_hour",
            field=models.PositiveSmallIntegerField(
                default=6,
                help_text="Preferred local hour (0-23) for host bank-agent scheduled sync.",
            ),
        ),
    ]
