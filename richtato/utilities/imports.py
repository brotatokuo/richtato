import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richtato.settings")
django.setup()

# from richtato.apps.expense.models import ExpenseDB
# from richtato.apps.income.models import IncomeDB
from asgiref.sync import sync_to_async

from richtato.apps.richtato_user.models import User
from utilities.db_model import DB


class RichtatoImporter:
    def __init__(self, user):
        self.user = user

    async def add_async(self, db_model: DB, data_list: list[dict]) -> None:
        """
        Asynchronously adds data to the given db_model (subclass of DB).

        Args:
            db_model (type[DB]): The database model to which data is added (e.g., CardAccountDB).
            data_list (list[dict]): A list of dictionaries with data to be added.

        Returns:
            None
        """
        for data in data_list:
            # Fetch user asynchronously based on the user_id in the data
            user = await sync_to_async(User.objects.get)(id=data["user_id"])
            for key, value in data.items():
                if key != "user_id":
                    # Ensure db_model.add can handle dynamic key-value addition
                    print(f"Adding {key} = {value} to {db_model}")
                    await sync_to_async(db_model.add)(user, {key: value})
