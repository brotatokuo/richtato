# Generated migration for teller app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TellerConnection",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "access_token",
                    models.CharField(
                        help_text="Encrypted Teller access token", max_length=255
                    ),
                ),
                (
                    "teller_account_id",
                    models.CharField(help_text="Teller account ID", max_length=255),
                ),
                (
                    "enrollment_id",
                    models.CharField(
                        blank=True, help_text="Teller enrollment ID", max_length=255
                    ),
                ),
                (
                    "institution_name",
                    models.CharField(help_text="Bank/institution name", max_length=255),
                ),
                (
                    "account_name",
                    models.CharField(
                        help_text="Account name or nickname", max_length=255
                    ),
                ),
                (
                    "account_type",
                    models.CharField(
                        blank=True,
                        help_text="Account type (checking, savings, etc.)",
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("disconnected", "Disconnected"),
                            ("error", "Error"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "last_sync",
                    models.DateTimeField(
                        blank=True,
                        help_text="Last successful sync timestamp",
                        null=True,
                    ),
                ),
                (
                    "last_sync_error",
                    models.TextField(
                        blank=True, help_text="Last sync error message if any"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teller_connections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "teller_connection",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="tellerconnection",
            index=models.Index(
                fields=["user", "status"], name="teller_conn_user_id_87c5a9_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="tellerconnection",
            index=models.Index(
                fields=["teller_account_id"], name="teller_conn_teller__6f4e1c_idx"
            ),
        ),
    ]
