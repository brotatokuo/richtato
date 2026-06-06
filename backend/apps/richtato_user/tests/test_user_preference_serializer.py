import pytest

from apps.richtato_user.models import User, UserPreference
from apps.richtato_user.serializers import UserPreferenceSerializer


@pytest.mark.django_db
class TestUserPreferenceSerializer:
    def test_platform_tour_completed_defaults_to_false(self):
        user = User.objects.create_user(username="tour-user", password="test-pass-123")
        prefs = UserPreference.objects.get(user=user)

        assert prefs.platform_tour_completed is False

        serializer = UserPreferenceSerializer(prefs)
        assert serializer.data["platform_tour_completed"] is False

    def test_platform_tour_completed_can_be_updated(self):
        user = User.objects.create_user(username="tour-user-2", password="test-pass-123")
        prefs = UserPreference.objects.get(user=user)

        serializer = UserPreferenceSerializer(
            prefs,
            data={"platform_tour_completed": True},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        prefs.refresh_from_db()
        assert prefs.platform_tour_completed is True
