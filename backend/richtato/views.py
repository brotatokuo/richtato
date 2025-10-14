from abc import ABC, abstractmethod

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseAPIView(APIView, ABC):
    """
    Base view class to handle field remapping logic.
    Child classes can define their own FIELD_REMAP and customize the logic.
    """

    @property
    def field_remap(self):
        """
        Default field remapping. Child classes should override this property.
        """
        return {}

    def apply_fieldmap(self, account):
        """
        Apply the FIELD_REMAP to rename the fields in the result data.
        """
        mapped_account = {}
        for key, value in account.items():
            mapped_key = self.field_remap.get(
                key, key
            )  # Default to the original key if no mapping exists
            mapped_account[mapped_key] = value
        return mapped_account

    @abstractmethod
    def get(self, request):
        """
        Handle GET requests.
        """
        pass

    @abstractmethod
    def post(self, request):
        """
        Handle POST requests.
        """
        pass

    @abstractmethod
    def patch(self, request, pk):
        """
        Handle PATCH requests.
        """
        pass

    @abstractmethod
    def delete(self, request):
        """
        Handle DELETE requests.
        """
        pass


def custom_404_view(request, exception):
    return Response(
        {"error": "Not Found", "message": "The requested resource was not found."},
        status=status.HTTP_404_NOT_FOUND,
    )


def custom_500_view(request):
    return Response(
        {
            "error": "Internal Server Error",
            "message": "An internal server error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
