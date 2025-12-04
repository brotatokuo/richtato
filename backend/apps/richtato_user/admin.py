from django.contrib import admin

from apps.richtato_user.models import User, UserPreference

# Register User models only - other models are registered in their respective apps
admin.site.register(User)
admin.site.register(UserPreference)
