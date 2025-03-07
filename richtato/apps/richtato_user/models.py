from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from loguru import logger
from utilities.db_model import DB
from utilities.tools import convert_currency_to_float


# Custom user manager
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150, unique=True
    )  # Primary and unique login field
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    import_path = models.CharField(max_length=100, default="", blank=True, null=True)
    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def networth(self):
        return sum(account.latest_balance for account in self.account.all())


class CardAccount(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="card_account"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.user}] {self.name}"


class CardAccountDB(DB):
    def __init__(self, user: User) -> None:
        self.user = user

    @classmethod
    def from_username(cls, username: str):
        user = User.objects.get(username=username)
        return cls(user)

    # @staticmethod
    # async def add_async(data_list: list[dict]) -> None:
    #     for data in data_list:
    #         user = await sync_to_async(User.objects.get)(id=data["user_id"])
    #         card_account_db = CardAccountDB(user)
    #         for key, value in data.items():
    #             if key != "user_id":
    #                 await sync_to_async(card_account_db.add)(key, value)

    # def add(self, card_attribute: str, card_value: str) -> None:
    #     if not hasattr(CardAccount, card_attribute):
    #         logger.error(
    #             f"Error: {card_attribute} does not exist on CardAccount model."
    #         )
    #         return
    #     if CardAccount.objects.filter(
    #         user=self.user, **{card_attribute: card_value}
    #     ).exists():
    #         logger.warning(f"{card_attribute} = {card_value} already exists.")
    #         return
    #     card_account = CardAccount(
    #         user=self.user, **{card_attribute: card_value.strip()}
    #     )
    #     card_account.save()
    #     print(f"Saved card account with {card_attribute} = {card_value}")
    def add(self, **kwargs) -> None:
        """
        Dynamically adds attributes and values to the CardAccount model.

        Args:
            **kwargs: Arbitrary keyword arguments representing attributes and values
                      to be added to the CardAccount model.
        """
        # Iterate through each key-value pair in kwargs
        for card_attribute, card_value in kwargs.items():
            # Check if the CardAccount model has the card_attribute
            if not hasattr(CardAccount, card_attribute):
                logger.error(
                    f"Error: {card_attribute} does not exist on CardAccount model."
                )
                return

            # Check if the record already exists for the given attribute and value
            if CardAccount.objects.filter(
                user=self.user, **{card_attribute: card_value}
            ).exists():
                logger.warning(f"{card_attribute} = {card_value} already exists.")
                return

            card_account = CardAccount(
                user=self.user, **{card_attribute: card_value.strip()}
            )
            card_account.save()
            logger.info(f"Saved card account with {card_attribute} = {card_value}")

    def delete(self, card_id: int) -> None:
        CardAccount.objects.get(id=card_id).delete()

    def update(self, card_id: int, card_name: str) -> None:
        CardAccount.objects.update_or_create(
            user=self.user, id=card_id, defaults={"name": card_name}
        )


class Category(models.Model):
    CATEGORY_TYPES = [
        ("essential", "Essential"),
        ("nonessential", "Non Essential"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    name = models.CharField(max_length=100)
    keywords = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50, choices=CATEGORY_TYPES, default="essential")
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"[{self.user}] {self.name}: {self.keywords}"


class CategoryDB:
    def __init__(self, user):
        self.user = user

    @classmethod
    def from_username(cls, username: str):
        user = User.objects.get(username=username)
        return cls(user)

    def add(
        self,
        category_name: str,
        keywords: list[str],
        budget: str,
        category_type: str,
        **extra_fields,
    ) -> None:
        """
        Add a new category with dynamic input options.

        Args:
            category_name (str): Name of the category.
            keywords (list[str]): List of keywords for the category.
            budget (str): Budget for the category.
            category_type (str): Type of the category.
            **extra_fields: Additional dynamic fields for Category model.

        Returns:
            None
        """
        if Category.objects.filter(user=self.user, name=category_name).exists():
            return

        dynamic_fields = {}
        for field, value in extra_fields.items():
            if hasattr(Category, field):
                dynamic_fields[field] = value
            else:
                logger.warning(f"Warning: {field} is not a valid field for Category.")

        category = Category(
            user=self.user,
            name=category_name.strip(),
            keywords=keywords,
            budget=convert_currency_to_float(budget),
            type=category_type,
            **dynamic_fields,
        )

        category.save()
        print(
            f"Saved category with name = {category_name}, and dynamic fields: {dynamic_fields}"
        )

    def delete(self, category_name: str) -> None:
        Category.objects.filter(user=self.user, name=category_name).delete()

    def update(
        self,
        category_name: str,
        category_keywords: list[str],
        category_budget: str,
        category_type: str,
        category_color: str,
    ) -> None:
        Category.objects.update_or_create(
            user=self.user,
            defaults={
                "name": category_name,
                "keywords": category_keywords,
                "budget": category_budget,
                "type": category_type,
                "color": category_color,
            },
        )
