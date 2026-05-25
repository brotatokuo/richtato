from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("richtato_user", "0004_remove_user_is_automation_runner"),
    ]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="bank_agent_fernet_key",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Stable Fernet key for the host bank-agent vault encryption.",
                max_length=64,
            ),
        ),
    ]
