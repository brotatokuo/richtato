from django.contrib import admin

from richtato.apps.account.models import Account
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income
from richtato.apps.budget.models import Budget
from richtato.apps.richtato_user.models import CardAccount, Category, User

# Register your models here.
admin.site.register(User)
admin.site.register(Account)
admin.site.register(Expense)
admin.site.register(Income)
admin.site.register(CardAccount)
admin.site.register(Category)
admin.site.register(Budget)
