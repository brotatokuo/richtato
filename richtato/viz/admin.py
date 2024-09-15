from django.contrib import admin
from .models import User, Category, Transaction
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(User, UserAdmin)  # Use Django's built-in UserAdmin
admin.site.register(Category)
admin.site.register(Transaction)