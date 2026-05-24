from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0017_statementfile_reconciliation_acknowledged_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="statementfile",
            name="drive_file_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
