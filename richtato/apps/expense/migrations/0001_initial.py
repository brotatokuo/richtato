# Generated by Django 4.2.18 on 2025-03-01 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Expense",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.CharField(max_length=100)),
                ("date", models.DateField(blank=True, null=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]
