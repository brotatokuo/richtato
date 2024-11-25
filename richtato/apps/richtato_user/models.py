from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


# Custom user manager
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"  # Email will be the unique identifier
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username


class CardAccount(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="card_account"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.user}] {self.name}"


class Category(models.Model):
    CATEGORY_TYPES = [
        ('essential', "Essential"),
        ('nonessential', "Non Essential"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    name = models.CharField(max_length=100)
    keywords = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    types = models.CharField(max_length=50, choices=CATEGORY_TYPES, default='essential')
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"[{self.user}] {self.name}: {self.keywords}"
