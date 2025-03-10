from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


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

    USERNAME_FIELD = "username"  # Only username is used for login
    REQUIRED_FIELDS = []  # No additional required fields for creating a superuser

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
