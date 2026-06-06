# Removes the deprecated is_automation_runner flag after the Playwright
# agent moved out of the Django app and into the standalone bank-agent CLI.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("richtato_user", "0003_alter_user_is_automation_runner"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="is_automation_runner",
        ),
    ]
