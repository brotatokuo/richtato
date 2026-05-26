from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0024_alter_accountbalancehistory_source"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="financialaccount",
            name="image_key",
        ),
    ]
