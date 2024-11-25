from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings, name='settings'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-card-account/', views.add_card_account, name='add_card_account'),
]