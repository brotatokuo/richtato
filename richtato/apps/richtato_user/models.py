from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    User,
)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from richtato.categories.categories import BaseCategory

supported_card_banks = [
    ("american_express", "American Express"),
    ("bank_of_america", "Bank of America"),
    ("bilt", "BILT"),
    ("chase", "Chase"),
    ("citibank", "Citibank"),
    ("other", "Other"),
]


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
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    import_path = models.CharField(max_length=100, default="", blank=True, null=True)
    objects = UserManager()

    USERNAME_FIELD = "username"  # Only username is used for login
    REQUIRED_FIELDS = []  # No additional required fields for creating a superuser

    def __str__(self):
        return self.username


class CardAccount(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="card_account"
    )
    name = models.CharField(max_length=100)
    bank = models.CharField(choices=supported_card_banks, max_length=50)

    def __str__(self):
        return f"[{self.user}] {self.name}"

    @property
    def card_bank_title(self):
        """Returns the human-readable bank name."""
        return dict(supported_card_banks).get(self.bank, self.bank)


class Category(models.Model):
    CATEGORY_TYPES = [
        ("essential", "Essential"),
        ("nonessential", "Non Essential"),
    ]
    supported_categories = [
        (category.name.replace("/", "_"), category.name)
        for category in BaseCategory._registered_categories
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100, choices=supported_categories)
    type = models.CharField(max_length=50, choices=CATEGORY_TYPES, default="essential")

    class Meta:
        unique_together = ("user", "name")
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"[{self.user}] {self.name} ({self.type})"

    @classmethod
    def create_default_categories_for_user(cls, user):
        """Create all supported categories for a user"""
        categories_to_create = []
        category_essentials = {
            "Travel": "nonessential",
            "Shopping": "nonessential",
            "Online Shopping": "nonessential",
            "Groceries": "essential",
            "Entertainment": "nonessential",
            "Utilities": "essential",
            "Housing": "essential",
            "Medical": "essential",
            "Education": "essential",
            "Savings": "essential",
            "Gifts": "nonessential",
            "Dining": "nonessential",
            "Investments": "essential",
            "Subscriptions": "nonessential",
            "Charity": "nonessential",
            "Pet": "nonessential",
            "Wholesale": "essential",
            "Car": "essential",
            "Phone": "essential",
            "Miscellaneous": "nonessential",
            "Payments": "essential",
        }

        for category_key, category_display in cls.supported_categories:
            # Check if category already exists for this user
            if not cls.objects.filter(user=user, name=category_key).exists():
                # You might want to set different defaults based on category
                categories_to_create.append(
                    cls(
                        user=user,
                        name=category_key,
                        type=category_essentials.get(category_key),
                    )
                )

        if categories_to_create:
            cls.objects.bulk_create(categories_to_create)

    @receiver(post_save, sender=User)
    def create_user_categories(sender, instance, created, **kwargs):
        """Signal to create categories when a new user is created"""
        if created:  # Only for newly created users
            Category.create_default_categories_for_user(instance)
