"""Unit tests for CategoryService."""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from apps.category.services.category_service import CategoryService
from apps.category.models import Category


class TestCategoryService(SimpleTestCase):
    """Test CategoryService business logic."""

    def setUp(self):
        self.mock_category_repo = MagicMock()
        self.service = CategoryService(category_repo=self.mock_category_repo)
        self.mock_user = MagicMock()

    def test_get_user_categories_formatted(self):
        """Test getting formatted categories for a user."""
        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.name = "Groceries"
        mock_cat1.type = "essential"
        mock_cat1.enabled = True

        mock_cat2 = MagicMock()
        mock_cat2.id = 2
        mock_cat2.name = "Dining"
        mock_cat2.type = "nonessential"
        mock_cat2.enabled = True

        self.mock_category_repo.get_user_categories.return_value = [
            mock_cat1,
            mock_cat2,
        ]

        result = self.service.get_user_categories_formatted(self.mock_user)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0],
            {"id": 1, "name": "Groceries", "type": "essential", "enabled": True},
        )
        self.assertEqual(
            result[1],
            {"id": 2, "name": "Dining", "type": "nonessential", "enabled": True},
        )

    def test_get_enabled_categories(self):
        """Test getting only enabled categories."""
        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.name = "Groceries"
        mock_cat1.type = "essential"

        self.mock_category_repo.get_user_categories.return_value = [mock_cat1]

        result = self.service.get_enabled_categories(self.mock_user)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"id": 1, "name": "Groceries", "type": "essential"})
        self.mock_category_repo.get_user_categories.assert_called_once_with(
            self.mock_user, enabled_only=True
        )

    def test_get_category_by_id_found(self):
        """Test getting a category by ID when it exists."""
        mock_cat = MagicMock()
        mock_cat.id = 1
        mock_cat.name = "Groceries"
        mock_cat.type = "essential"
        mock_cat.enabled = True
        self.mock_category_repo.get_by_id.return_value = mock_cat

        result = self.service.get_category_by_id(1, self.mock_user)

        self.assertEqual(
            result, {"id": 1, "name": "Groceries", "type": "essential", "enabled": True}
        )

    def test_get_category_by_id_not_found(self):
        """Test getting a category by ID when it doesn't exist."""
        self.mock_category_repo.get_by_id.return_value = None

        result = self.service.get_category_by_id(999, self.mock_user)

        self.assertIsNone(result)

    def test_create_category(self):
        """Test creating a new category."""
        mock_cat = MagicMock()
        mock_cat.id = 1
        mock_cat.name = "New Category"
        mock_cat.type = "essential"
        mock_cat.enabled = True
        self.mock_category_repo.create_category.return_value = mock_cat

        result = self.service.create_category(
            self.mock_user, "New Category", "essential", True
        )

        self.assertEqual(
            result,
            {"id": 1, "name": "New Category", "type": "essential", "enabled": True},
        )
        self.mock_category_repo.create_category.assert_called_once_with(
            self.mock_user, "New Category", "essential", True
        )

    def test_update_category_success(self):
        """Test updating a category successfully."""
        mock_cat = MagicMock()
        updated_cat = MagicMock()
        updated_cat.id = 1
        updated_cat.name = "Updated Category"
        updated_cat.type = "nonessential"
        updated_cat.enabled = False

        self.mock_category_repo.get_by_id.return_value = mock_cat
        self.mock_category_repo.update_category.return_value = updated_cat

        result = self.service.update_category(
            1, self.mock_user, type="nonessential", enabled=False
        )

        self.assertEqual(
            result,
            {
                "id": 1,
                "name": "Updated Category",
                "type": "nonessential",
                "enabled": False,
            },
        )

    def test_update_category_not_found(self):
        """Test updating a category that doesn't exist."""
        self.mock_category_repo.get_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_category(999, self.mock_user, enabled=False)

        self.assertEqual(str(context.exception), "Category not found")

    def test_delete_category_success(self):
        """Test deleting a category successfully."""
        mock_cat = MagicMock()
        self.mock_category_repo.get_by_id.return_value = mock_cat

        self.service.delete_category(1, self.mock_user)

        self.mock_category_repo.delete_category.assert_called_once_with(mock_cat)

    def test_delete_category_not_found(self):
        """Test deleting a category that doesn't exist."""
        self.mock_category_repo.get_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.delete_category(999, self.mock_user)

        self.assertEqual(str(context.exception), "Category not found")

    def test_get_category_settings(self):
        """Test getting category settings."""
        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.name = "Groceries"
        mock_cat1.type = "essential"
        mock_cat1.enabled = True

        self.mock_category_repo.get_user_categories.return_value = [mock_cat1]

        result = self.service.get_category_settings(self.mock_user)

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0],
            {
                "id": 1,
                "name": "Groceries",
                "type": "essential",
                "enabled": True,
            },
        )

    def test_bulk_update_category_settings(self):
        """Test bulk updating category settings."""
        mock_cat1 = MagicMock()
        mock_cat1.id = 1
        mock_cat1.name = "Groceries"
        mock_cat1.type = "essential"
        mock_cat1.enabled = True

        self.mock_category_repo.get_by_id.return_value = mock_cat1

        settings = [{"id": 1, "enabled": False}]
        result = self.service.bulk_update_category_settings(self.mock_user, settings)

        self.assertEqual(len(result), 1)
        self.mock_category_repo.update_category.assert_called_once_with(
            mock_cat1, enabled=False
        )

    def test_create_default_categories_for_user(self):
        """Test creating default categories for a new user."""
        # Test that the method calls repository methods correctly
        # For simplicity, we'll just verify the repo is called for checking existence
        self.mock_category_repo.category_exists_for_user.return_value = True

        # Call with all categories already existing - should not create any
        self.service.create_default_categories_for_user(self.mock_user)

        # Should check for existence but not call bulk_create
        self.assertTrue(self.mock_category_repo.category_exists_for_user.called)
        self.mock_category_repo.bulk_create_categories.assert_not_called()

    def test_get_field_choices(self):
        """Test getting field choices for Category."""
        result = self.service.get_field_choices()

        self.assertIn("type", result)
        self.assertIn("name", result)
        self.assertEqual(len(result["type"]), 2)
        self.assertEqual(result["type"][0]["value"], "essential")
