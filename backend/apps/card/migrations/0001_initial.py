# Generated migration for Card app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # This model already exists in the database as richtato_user_cardaccount
        # We're just declaring it here for Django to recognize it in the card app
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="CardAccount",
                    fields=[
                        ("id", models.AutoField(primary_key=True, serialize=False)),
                        ("name", models.CharField(max_length=100)),
                        ("bank", models.CharField(max_length=50)),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="card_account",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "richtato_user_cardaccount",
                    },
                ),
            ],
            database_operations=[
                # No database operations - table already exists
            ],
        ),
    ]
