import os

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor


class PostgresClient:
    def __init__(self):
        deploy_stage = os.environ.get("DEPLOY_STAGE", "DEV")
        connection_string = (
            os.environ.get("PROD_DATABASE_URL")
            if deploy_stage == "PROD"
            else os.environ.get("DEV_DATABASE_URL")
        )
        self.conn = psycopg2.connect(connection_string)

    def query(self, sql, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            if cursor.description:  # Means query returned rows
                return cursor.fetchall()
            else:
                self.conn.commit()
                return None

    def get_expense_df(self, user_id: int) -> pd.DataFrame:
        sql = """
            SELECT
                e.*,
                c.name AS category_name,
                a.name AS account_name
            FROM public.expense_expense e
            JOIN public.richtato_user_category c ON e.category_id = c.id
            JOIN public.richtato_user_cardaccount a ON e.account_name_id = a.id
            WHERE e.user_id = %s
            ORDER BY e.date DESC;
        """
        rows = self.query(sql, (user_id,))
        if rows:
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            return df
        else:
            return pd.DataFrame()

    def close(self):
        self.conn.close()
