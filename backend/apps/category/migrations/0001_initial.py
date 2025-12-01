# Generated migration for Category app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # This model already exists in the database as richtato_user_category
        # We're just declaring it here for Django to recognize it in the category app
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Category",
                    fields=[
                        ("id", models.AutoField(primary_key=True, serialize=False)),
                        ("name", models.CharField(max_length=100)),
                        ("type", models.CharField(default="essential", max_length=50)),
                        ("enabled", models.BooleanField(default=True)),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="categories",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "richtato_user_category",
                        "verbose_name_plural": "Categories",
                    },
                ),
                migrations.AlterUniqueTogether(
                    name="category",
                    unique_together={("user", "name")},
                ),
            ],
            database_operations=[
                # No database operations - table already exists
            ],
        ),
    ]
