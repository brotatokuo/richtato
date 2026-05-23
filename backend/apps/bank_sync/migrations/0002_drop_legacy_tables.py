"""Drop the legacy bank_automation tables and clean ``django_migrations`` rows.

The previous Chrome-extension-driven flow lived in the ``apps.bank_automation``
Django app, which is being removed wholesale. Because the app is no longer
in ``INSTALLED_APPS``, Django will not generate migrations to drop its
tables — we have to do it ourselves.

This is forward-only (``RunSQL`` with ``noop`` reverse) and idempotent
(every statement is ``IF EXISTS`` guarded) so it is safe to run on fresh
checkouts that never had the legacy tables.
"""

from django.db import migrations


def _drop_legacy_django_migrations(apps, schema_editor):
    """Remove ``django_migrations`` rows for the deleted ``bank_automation`` app.

    Without this, ``manage.py migrate`` keeps reporting "app X has unapplied
    migrations" warnings even though the app is gone. The rows are pure
    history; dropping them does not affect any current schema.
    """

    schema_editor.execute("DELETE FROM django_migrations WHERE app = 'bank_automation';")


class Migration(migrations.Migration):
    dependencies = [
        ("bank_sync", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS bank_session;",
                "DROP TABLE IF EXISTS bank_account_link;",
                "DROP TABLE IF EXISTS bank_automation_run;",
                "DROP TABLE IF EXISTS bank_connection;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunPython(_drop_legacy_django_migrations, migrations.RunPython.noop),
    ]
