# Generated migration for cleanup
# Removes Merchant model and merchant field from Transaction

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transaction", "0004_alter_keywordrule_unique_together_and_more"),
    ]

    operations = [
        # Remove the merchant field from Transaction
        migrations.RemoveField(
            model_name="transaction",
            name="merchant",
        ),
        # Remove foreign key from Merchant before deleting
        migrations.RemoveField(
            model_name="merchant",
            name="category_hint",
        ),
        # Delete the Merchant model
        migrations.DeleteModel(
            name="Merchant",
        ),
    ]
