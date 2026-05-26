import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0014_storage_uri_statement_source"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GoogleDriveConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("google_account_email", models.EmailField(blank=True, default="", max_length=254)),
                ("refresh_token_encrypted", models.TextField(blank=True, default="")),
                ("root_folder_id", models.CharField(blank=True, default="", max_length=255)),
                ("root_folder_name", models.CharField(blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=False)),
                ("connected_at", models.DateTimeField(blank=True, null=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("disconnected_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="google_drive_connection",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "google_drive_connection",
                "indexes": [
                    models.Index(fields=["user", "is_active"], name="google_driv_user_id_7ba611_idx"),
                    models.Index(fields=["root_folder_id"], name="google_driv_root_fo_fe125a_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="GoogleDriveAccountFolder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("folder_id", models.CharField(max_length=255, unique=True)),
                ("folder_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="google_drive_folder",
                        to="financial_account.financialaccount",
                    ),
                ),
                (
                    "connection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="account_folders",
                        to="financial_account.googledriveconnection",
                    ),
                ),
            ],
            options={
                "db_table": "google_drive_account_folder",
                "indexes": [
                    models.Index(
                        fields=["connection", "account"],
                        name="google_driv_connect_6eb2f1_idx",
                    ),
                ],
            },
        ),
    ]
