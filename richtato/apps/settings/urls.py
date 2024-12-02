from django.urls import path

from . import views

urlpatterns = [
    path('', views.settings, name='settings'),

    # Card Account
    path('get-cards/', views.get_cards, name='get_cards'),
    path('add-card/', views.add_card, name='add_card'),
    path('update-cards/', views.update_cards, name='update_cards'),

    # Account
    path('get-accounts/', views.get_accounts, name='get_accounts'),
    path('add-account/', views.add_account, name='add_account'),
    path('update-accounts/', views.update_accounts, name='update_accounts'),

    # Categories
    path('get-categories/', views.get_categories, name='get_categories'),
    path('add-category/', views.add_category, name='add_category'),
    path('update-categories/', views.update_categories, name='update_categories'),
    
]