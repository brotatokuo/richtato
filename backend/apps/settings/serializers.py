from rest_framework import serializers

from .models import CardAccount


class CardAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardAccount
        fields = ["id", "name", "bank"]

        read_only_fields = ["id"]
