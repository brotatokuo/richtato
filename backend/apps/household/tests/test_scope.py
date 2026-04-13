"""Tests for get_scope_user_ids utility."""

from unittest.mock import MagicMock

from apps.household.scope import get_scope_user_ids


class TestGetScopeUserIds:
    def _make_request(self, user, scope="personal"):
        request = MagicMock()
        request.user = user
        request.query_params = {"scope": scope}
        return request

    def test_personal_scope_returns_single_user_id(self, user_a):
        request = self._make_request(user_a, "personal")
        assert get_scope_user_ids(request) == [user_a.id]

    def test_household_scope_returns_all_member_ids(self, user_a, user_b, household_with_both):
        request = self._make_request(user_a, "household")
        ids = get_scope_user_ids(request)
        assert set(ids) == {user_a.id, user_b.id}

    def test_household_scope_falls_back_to_personal_if_no_membership(self, user_b):
        request = self._make_request(user_b, "household")
        assert get_scope_user_ids(request) == [user_b.id]

    def test_invalid_scope_value_defaults_to_personal(self, user_a, household):
        request = self._make_request(user_a, "garbage")
        assert get_scope_user_ids(request) == [user_a.id]
