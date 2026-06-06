from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0016_alter_financialaccount_storage_uri"),
    ]

    operations = [
        migrations.AddField(
            model_name="statementfile",
            name="reconciliation_acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
