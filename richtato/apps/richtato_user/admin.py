from django.contrib import admin
from apps.richtato_user.models import User
from apps.account.models import Account
from apps.expense.models import Expense
from apps.income.models import Income

# Register your models here.
admin.site.register(User)
admin.site.register(Account)
admin.site.register(Expense)
admin.site.register(Income)
