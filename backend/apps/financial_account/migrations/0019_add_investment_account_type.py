from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0018_statementfile_drive_file_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="financialaccount",
            name="account_type",
            field=models.CharField(
                choices=[
                    ("checking", "Checking Account"),
                    ("savings", "Savings Account"),
                    ("credit_card", "Credit Card"),
                    ("investment", "Investment Account"),
                ],
                default="checking",
                max_length=20,
            ),
        ),
    ]
