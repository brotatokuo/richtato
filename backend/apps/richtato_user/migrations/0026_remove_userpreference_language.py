# Migration to remove language field from UserPreference

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("richtato_user", "0025_remove_category_cardaccount"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userpreference",
            name="language",
        ),
    ]
