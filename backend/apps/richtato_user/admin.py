from django.contrib import admin

from apps.richtato_user.models import User, UserPreference
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.transaction.models import Transaction, TransactionCategory, Merchant
from apps.budget.models import Budget, BudgetCategory

# Register User models
admin.site.register(User)
admin.site.register(UserPreference)

# Register Financial Account models
admin.site.register(FinancialAccount)
admin.site.register(FinancialInstitution)

# Register Transaction models
admin.site.register(Transaction)
admin.site.register(TransactionCategory)
admin.site.register(Merchant)

# Register Budget models
admin.site.register(Budget)
admin.site.register(BudgetCategory)
