# Generated for storage_uri + StatementFile.source.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0013_financialaccount_sync_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialaccount",
            name="storage_uri",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Storage URI for this account's statement files. Empty defaults to "
                    "file:///<repo>/local_data/statements/<user_id>/<account_id>/. "
                    "Supports file:// today; gdrive:// later."
                ),
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="statementfile",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual_upload", "Manual Upload"),
                    ("agent_drop", "Agent Drop"),
                    ("unknown", "Unknown"),
                ],
                default="manual_upload",
                help_text=(
                    "How this statement entered the library: manual_upload via the "
                    "UI, agent_drop via the host bank-agent + storage scanner, or "
                    "unknown."
                ),
                max_length=20,
            ),
        ),
    ]
