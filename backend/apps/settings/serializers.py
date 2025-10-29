from apps.richtato_user.models import CardAccount
from rest_framework import serializers


class CardAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardAccount
        fields = ["id", "name", "bank"]

        read_only_fields = ["id"]
