# views.py
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account
from .serializers import AccountSerializer


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class AccountAPIView(APIView):
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Assign user manually
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            account = Account.objects.get(pk=pk, user=request.user)
        except Account.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AccountSerializer(account, data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            account = Account.objects.get(pk=pk, user=request.user)
            account.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Account.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
