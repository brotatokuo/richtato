"""Drop the legacy ``bank_sync`` tables after removing the app.

The ``apps.bank_sync`` Django app (``bank_login``, ``synced_account``,
``bank_sync_run``) has been deleted along with the Playwright bank-agent.
Drop its tables in child-to-parent order so no CASCADE is required (keeps
this compatible with both PostgreSQL and SQLite). Tables may not exist on
fresh databases, so each drop is guarded with ``IF EXISTS``.
"""

from django.db import migrations

_DROP_SQL = """
DROP TABLE IF EXISTS bank_sync_run;
DROP TABLE IF EXISTS synced_account;
DROP TABLE IF EXISTS bank_login;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("financial_account", "0026_remove_financialaccount_agent_activity_url_encrypted_and_more"),
    ]

    operations = [
        migrations.RunSQL(_DROP_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
