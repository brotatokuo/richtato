from apps.budget.models import Budget
from apps.richtato_user.models import User
from apps.category.models import Category
from rest_framework import serializers


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

    def validate(self, attrs):
        user = attrs.get("user") or getattr(self.instance, "user", None)
        category = attrs.get("category") or getattr(self.instance, "category", None)
        if user and category:
            qs = Budget.objects.filter(user=user, category=category)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "A budget already exists for this category. Update the existing budget instead."
                )
        return attrs
