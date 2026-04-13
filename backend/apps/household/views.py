"""Views for household API."""

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.household.serializers import (
    HouseholdCreateSerializer,
    HouseholdSerializer,
    JoinHouseholdSerializer,
)
from apps.household.services.household_service import HouseholdService


class HouseholdAPIView(APIView):
    """Get or create the current user's household."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = HouseholdService()

    def get(self, request):
        household = self.service.get_household(request.user)
        if not household:
            return Response(
                {"error": "You are not a member of any household."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = HouseholdSerializer(household)
        return Response(serializer.data)

    def post(self, request):
        serializer = HouseholdCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            household = self.service.create_household(
                user=request.user,
                name=serializer.validated_data["name"],
            )
            return Response(
                HouseholdSerializer(household).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HouseholdInviteAPIView(APIView):
    """Generate an invite code for the household."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = HouseholdService()

    def post(self, request):
        try:
            result = self.service.generate_invite_code(request.user)
            return Response(
                {
                    "invite_code": result["invite_code"],
                    "expires_at": result["expires_at"].isoformat(),
                },
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HouseholdJoinAPIView(APIView):
    """Join a household using an invite code."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = HouseholdService()

    def post(self, request):
        serializer = JoinHouseholdSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            household = self.service.join_household(
                user=request.user,
                invite_code=serializer.validated_data["code"],
            )
            return Response(HouseholdSerializer(household).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HouseholdLeaveAPIView(APIView):
    """Leave the current household."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = HouseholdService()

    def post(self, request):
        try:
            self.service.leave_household(request.user)
            return Response({"message": "Left household successfully."})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HouseholdMembersAPIView(APIView):
    """List household members."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = HouseholdService()

    def get(self, request):
        members = self.service.get_members(request.user)
        return Response({"members": members})
