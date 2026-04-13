"""Utility for resolving the query scope (personal vs household)."""

from apps.household.models import HouseholdMember


def get_scope_user_ids(request) -> list[int]:
    """Return user IDs to query against based on the `scope` query parameter.

    - ``personal`` (default): only the requesting user
    - ``household``: all members of the user's household (falls back to personal)
    """
    scope = request.query_params.get("scope", "personal")
    if scope == "household":
        try:
            membership = HouseholdMember.objects.select_related("household").get(user=request.user)
            return list(
                membership.household.members.values_list("user_id", flat=True)
            )
        except HouseholdMember.DoesNotExist:
            pass
    return [request.user.id]
