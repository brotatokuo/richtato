"""Service layer for User operations."""

from django.contrib.auth import authenticate
from apps.richtato_user.repositories.user_repository import UserRepository


class UserService:
    """Service for User business logic."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
    ):
        self.user_repo = user_repo or UserRepository()

    def authenticate_user(self, username: str, password: str):
        """Authenticate a user with username and password."""
        return authenticate(username=username, password=password)

    def check_username_availability(self, username: str) -> bool:
        """Check if a username is available."""
        return not self.user_repo.username_exists(username)

    def create_user(self, username: str, password: str, **extra_fields):
        """Create a new user account."""
        return self.user_repo.create_user(username, password, **extra_fields)

    def get_user_by_id(self, user_id: int):
        """Get a user by ID."""
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str):
        """Get a user by username."""
        return self.user_repo.get_by_username(username)

    def update_username(self, user, new_username: str):
        """Update a user's username."""
        if self.user_repo.username_exists(new_username):
            raise ValueError("Username already exists")
        return self.user_repo.update_user(user, username=new_username)

    def update_password(self, user, new_password: str):
        """Update a user's password."""
        user.set_password(new_password)
        user.save()
        return user

    def delete_user(self, user):
        """Delete a user account."""
        self.user_repo.delete_user(user)

    def get_user_profile_data(self, user) -> dict:
        """Get user profile data."""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email or "",
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "is_demo": user.is_demo,
        }
