"""Remove Plaid sync source choices and drop legacy sync tables."""

from django.db import migrations, models


def remap_plaid_sources_forward(apps, schema_editor):
    """Remap legacy 'plaid' / 'plaid_sync' source values to 'manual'."""
    FinancialAccount = apps.get_model("financial_account", "FinancialAccount")
    AccountBalanceHistory = apps.get_model("financial_account", "AccountBalanceHistory")

    FinancialAccount.objects.filter(sync_source="plaid").update(sync_source="manual")
    AccountBalanceHistory.objects.filter(source="plaid_sync").update(source="manual")


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0011_statementfile"),
    ]

    operations = [
        migrations.RunPython(remap_plaid_sources_forward, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="financialaccount",
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
        migrations.AlterField(
            model_name="accountbalancehistory",
            name="source",
            field=models.CharField(
                choices=[
                    ("transaction", "Transaction"),
                    ("manual", "Manual"),
                    ("csv_import", "CSV Import"),
                ],
                default="transaction",
                max_length=20,
            ),
        ),
        # Drop legacy sync tables. The apps.sync app has been removed entirely;
        # this is a forward-only cleanup. Tables may not exist on fresh
        # installs, so each statement is IF EXISTS guarded.
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS user_sync_status;",
                "DROP TABLE IF EXISTS sync_job;",
                "DROP TABLE IF EXISTS sync_connection;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
