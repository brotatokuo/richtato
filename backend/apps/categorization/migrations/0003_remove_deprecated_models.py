# Generated migration for cleanup
# Removes deprecated CategorizationRule and UserCategorizationPreference models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("categorization", "0002_initial"),
    ]

    operations = [
        # Remove the rule field from CategorizationHistory
        migrations.RemoveField(
            model_name="categorizationhistory",
            name="rule",
        ),
        # Remove foreign keys from CategorizationRule before deleting
        migrations.RemoveField(
            model_name="categorizationrule",
            name="category",
        ),
        migrations.RemoveField(
            model_name="categorizationrule",
            name="user",
        ),
        # Remove foreign keys from UserCategorizationPreference before deleting
        migrations.RemoveField(
            model_name="usercategorizationpreference",
            name="merchant",
        ),
        migrations.RemoveField(
            model_name="usercategorizationpreference",
            name="preferred_category",
        ),
        migrations.RemoveField(
            model_name="usercategorizationpreference",
            name="user",
        ),
        # Delete the deprecated models
        migrations.DeleteModel(
            name="CategorizationRule",
        ),
        migrations.DeleteModel(
            name="UserCategorizationPreference",
        ),
    ]
