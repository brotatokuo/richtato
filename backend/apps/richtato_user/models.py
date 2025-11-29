"""User authentication models for Richtato application."""

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
    """Custom user model for Richtato application."""

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Import/migration field - stores path to user's CSV import directory
    import_path = models.CharField(
        max_length=100,
        default="",
        blank=True,
        null=True,
        help_text="Directory path for CSV data imports",
    )

    # Demo user fields - for temporary trial accounts
    is_demo = models.BooleanField(
        default=False, help_text="Whether this is a temporary demo account"
    )
    demo_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Expiration timestamp for demo accounts"
    )

    objects = UserManager()

    USERNAME_FIELD = "username"  # Only username is used for login
    REQUIRED_FIELDS = []  # No additional required fields for creating a superuser

    def __str__(self):
        return self.username


class UserPreference(models.Model):
    """User preferences and settings."""

    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("system", "System"),
    ]

    DATE_FORMAT_CHOICES = [
        ("MM/DD/YYYY", "MM/DD/YYYY"),
        ("DD/MM/YYYY", "DD/MM/YYYY"),
        ("YYYY-MM-DD", "YYYY-MM-DD"),
    ]

    CURRENCY_CHOICES = [
        ("USD", "USD ($)"),
        ("EUR", "EUR (€)"),
        ("GBP", "GBP (£)"),
        ("CAD", "CAD (C$)"),
        ("AUD", "AUD (A$)"),
        ("JPY", "JPY (¥)"),
        ("CNY", "CNY (¥)"),
        ("INR", "INR (₹)"),
    ]

    TIMEZONE_CHOICES = [
        ("UTC", "UTC"),
        ("America/New_York", "Eastern Time"),
        ("America/Chicago", "Central Time"),
        ("America/Denver", "Mountain Time"),
        ("America/Los_Angeles", "Pacific Time"),
        ("Europe/London", "London"),
        ("Europe/Paris", "Paris"),
        ("Europe/Berlin", "Berlin"),
        ("Asia/Tokyo", "Tokyo"),
        ("Asia/Shanghai", "Shanghai"),
        ("Asia/Singapore", "Singapore"),
        ("Australia/Sydney", "Sydney"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences"
    )

    # Display preferences
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default="system",
        help_text="UI theme preference",
    )

    # Regional preferences
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Preferred currency code (e.g., USD, EUR, GBP)",
    )
    date_format = models.CharField(
        max_length=20,
        choices=DATE_FORMAT_CHOICES,
        default="MM/DD/YYYY",
        help_text="Preferred date display format",
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="User timezone (e.g., America/New_York, Europe/London)",
    )

    # Notification preferences
    notifications_enabled = models.BooleanField(
        default=True, help_text="Whether to receive notifications"
    )

    class Meta:
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user}"
