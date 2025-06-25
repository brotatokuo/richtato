from rest_framework import serializers

from richtato.apps.budget.models import Budget
from richtato.apps.richtato_user.models import Category, User


class BudgetSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Budget
        fields = [
            "id",
            "user",
            "category",
            "start_date",
            "end_date",
            "amount",
        ]
        read_only_fields = ["id"]
