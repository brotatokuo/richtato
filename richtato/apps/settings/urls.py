from django.urls import path

from . import views

urlpatterns = [
    path('', views.settings, name='settings'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-card/', views.add_card, name='add_card'),


    path('get-card-settings-data/', views.get_card_data, name='get_card_data'),
    path('get-accounts-data', views.get_accounts_data, name='get_accounts_data'),
    path('get-categories-data/', views.get_categories_data, name='get_categories_data'),
    
    path('update-accounts/', views.update_accounts, name='update_accounts'),
    path('update-categories/', views.update_categories, name='update_categories'),
    path('update-card-settings/', views.update_card_account, name='update_card_settings'),

]