"""Repository for User data access."""

from django.db.models import QuerySet
from apps.richtato_user.models import User


class UserRepository:
    """Repository for User data access - ORM layer only."""

    def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def username_exists(self, username: str) -> bool:
        """Check if a username exists."""
        return User.objects.filter(username=username).exists()

    def create_user(self, username: str, password: str, **extra_fields) -> User:
        """Create a new user."""
        user = User.objects.create_user(
            username=username, password=password, **extra_fields
        )
        return user

    def update_user(self, user: User, **data) -> User:
        """Update user fields."""
        for key, value in data.items():
            setattr(user, key, value)
        user.save()
        return user

    def delete_user(self, user: User) -> None:
        """Delete a user."""
        user.delete()

    def get_demo_users(self) -> QuerySet[User]:
        """Get all demo users."""
        return User.objects.filter(is_demo=True)
