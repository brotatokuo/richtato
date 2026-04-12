from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financial_account", "0008_negate_liability_balances"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountbalancehistory",
            name="source",
            field=models.CharField(
                choices=[
                    ("transaction", "Transaction"),
                    ("manual", "Manual"),
                    ("csv_import", "CSV Import"),
                    ("plaid_sync", "Plaid Sync"),
                ],
                default="transaction",
                max_length=20,
            ),
        ),
    ]
