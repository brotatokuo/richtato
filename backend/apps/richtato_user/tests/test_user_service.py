"""Unit tests for UserService."""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from apps.richtato_user.services.user_service import UserService


class TestUserService(SimpleTestCase):
    """Test UserService business logic."""

    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.service = UserService(user_repo=self.mock_user_repo)

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        with patch(
            "apps.richtato_user.services.user_service.authenticate"
        ) as mock_auth:
            mock_user = MagicMock()
            mock_auth.return_value = mock_user

            result = self.service.authenticate_user("testuser", "password123")

            self.assertEqual(result, mock_user)
            mock_auth.assert_called_once_with(
                username="testuser", password="password123"
            )

    def test_check_username_availability_available(self):
        """Test checking username availability when username is available."""
        self.mock_user_repo.username_exists.return_value = False

        result = self.service.check_username_availability("newuser")

        self.assertTrue(result)
        self.mock_user_repo.username_exists.assert_called_once_with("newuser")

    def test_check_username_availability_taken(self):
        """Test checking username availability when username is taken."""
        self.mock_user_repo.username_exists.return_value = True

        result = self.service.check_username_availability("existinguser")

        self.assertFalse(result)
        self.mock_user_repo.username_exists.assert_called_once_with("existinguser")

    def test_create_user(self):
        """Test creating a new user."""
        mock_user = MagicMock()
        self.mock_user_repo.create_user.return_value = mock_user

        result = self.service.create_user(
            "testuser", "password123", email="test@example.com"
        )

        self.assertEqual(result, mock_user)
        self.mock_user_repo.create_user.assert_called_once_with(
            "testuser", "password123", email="test@example.com"
        )

    def test_get_user_by_id(self):
        """Test getting a user by ID."""
        mock_user = MagicMock()
        self.mock_user_repo.get_by_id.return_value = mock_user

        result = self.service.get_user_by_id(1)

        self.assertEqual(result, mock_user)
        self.mock_user_repo.get_by_id.assert_called_once_with(1)

    def test_update_username_success(self):
        """Test updating username successfully."""
        mock_user = MagicMock()
        self.mock_user_repo.username_exists.return_value = False
        self.mock_user_repo.update_user.return_value = mock_user

        result = self.service.update_username(mock_user, "newusername")

        self.assertEqual(result, mock_user)
        self.mock_user_repo.username_exists.assert_called_once_with("newusername")
        self.mock_user_repo.update_user.assert_called_once_with(
            mock_user, username="newusername"
        )

    def test_update_username_already_exists(self):
        """Test updating username when new username already exists."""
        mock_user = MagicMock()
        self.mock_user_repo.username_exists.return_value = True

        with self.assertRaises(ValueError) as context:
            self.service.update_username(mock_user, "existinguser")

        self.assertEqual(str(context.exception), "Username already exists")
        self.mock_user_repo.username_exists.assert_called_once_with("existinguser")

    def test_update_password(self):
        """Test updating user password."""
        mock_user = MagicMock()

        result = self.service.update_password(mock_user, "newpassword123")

        self.assertEqual(result, mock_user)
        mock_user.set_password.assert_called_once_with("newpassword123")
        mock_user.save.assert_called_once()

    def test_delete_user(self):
        """Test deleting a user."""
        mock_user = MagicMock()

        self.service.delete_user(mock_user)

        self.mock_user_repo.delete_user.assert_called_once_with(mock_user)

    def test_get_user_profile_data(self):
        """Test getting user profile data."""
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.date_joined = MagicMock()
        mock_user.date_joined.isoformat.return_value = "2025-01-01T00:00:00"
        mock_user.is_demo = False

        result = self.service.get_user_profile_data(mock_user)

        self.assertEqual(
            result,
            {
                "id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "date_joined": "2025-01-01T00:00:00",
                "is_demo": False,
            },
        )
