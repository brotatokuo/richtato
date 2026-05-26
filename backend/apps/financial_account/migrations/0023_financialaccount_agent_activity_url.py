from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0022_financialaccount_agent_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialaccount",
            name="agent_activity_url_encrypted",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Encrypted bank-side activity URL used by the host bank-agent.",
            ),
        ),
    ]
