from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(User, UserAdmin)  # Use Django's built-in UserAdmin
admin.site.register(Account)
admin.site.register(AccountHistory)
admin.site.register(Category)
admin.site.register(CardAccount)
admin.site.register(Transaction)
admin.site.register(Earning)
