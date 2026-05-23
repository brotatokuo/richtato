"""Remove Plaid from Transaction.sync_source choices."""

from django.db import migrations, models


def remap_plaid_sync_source_forward(apps, schema_editor):
    """Remap legacy 'plaid' sync_source values on Transaction to 'manual'."""
    Transaction = apps.get_model("transaction", "Transaction")
    Transaction.objects.filter(sync_source="plaid").update(sync_source="manual")


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0003_add_is_deleted"),
    ]

    operations = [
        migrations.RunPython(remap_plaid_sync_source_forward, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="transaction",
            name="external_id",
            field=models.CharField(
                blank=True,
                help_text="External ID from sync source",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="sync_source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual Entry"),
                    ("csv", "CSV Import"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
    ]
