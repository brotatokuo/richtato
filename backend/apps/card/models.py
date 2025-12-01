"""CardAccount model for credit/debit card tracking."""

from django.conf import settings
from django.db import models

from .constants import SUPPORTED_CARD_BANKS


class CardAccount(models.Model):
    """Card account model for tracking credit and debit cards."""

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="card_account"
    )
    name = models.CharField(max_length=100)
    bank = models.CharField(choices=SUPPORTED_CARD_BANKS, max_length=50)

    class Meta:
        # Keep existing database table name for backward compatibility
        db_table = "richtato_user_cardaccount"

    def __str__(self):
        return f"[{self.user}] {self.name}"

    @property
    def card_bank_title(self):
        """Returns the human-readable bank name."""
        return dict(SUPPORTED_CARD_BANKS).get(self.bank, self.bank)
