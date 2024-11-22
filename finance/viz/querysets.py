from django.db import models

class TransactionQuerySet(models.QuerySet):
    def spending_dates(self, user):
        return self.filter(user=user).exclude(date__isnull=True).values_list('date', flat=True).distinct()