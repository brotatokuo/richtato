from django.urls import path

from . import views

page_name = 'settings'
urlpatterns = [
    path('', views.main, name=page_name),

    # Card Account
    path('get-cards/', views.get_cards, name=f'{page_name}_get_cards'),
    path('add-card/', views.add_card, name=f'{page_name}_add_card'),
    path('update-cards/', views.update_cards, name=f'{page_name}_update_cards'),

    # Account
    path('get-accounts/', views.get_accounts, name=f'{page_name}_get_accounts'),
    path('add-account/', views.add_account, name=f'{page_name}_add_account'),
    path('update-accounts/', views.update_accounts, name=f'{page_name}_update_accounts'),

    # Categories
    path('get-categories/', views.get_categories, name=f'{page_name}_get_categories'),
    path('add-category/', views.add_category, name=f'{page_name}_add_category'),
    path('update-categories/', views.update_categories, name=f'{page_name}_update_categories'),
    
    # Import
    path('generate-csv-templates/', views.generate_csv_templates, name=f'{page_name}_generate_csv_templates'),
    path('import-csv/', views.import_csv, name=f'{page_name}_import_csv'),

    # Google Sheets
    path('generate-google-sheets-templates/', views.generate_google_sheets_templates, name=f'{page_name}_generate_google_sheets_templates'),
    path('import-google-sheets-data', views.import_google_sheets_data, name=f'{page_name}_import_google_sheets_data'),
    path('export-google-sheets-data', views.export_google_sheets_data, name=f'{page_name}_export_google_sheets_data'),
]