from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense, name='expense'),
    path('add-expense-entry/', views.add_expense_entry, name='add_expense_entry'),
    path('get-plot-data/<int:year>/', views.get_expense_plot_data, name='get_expense_plot_data'),
    path('get-table-data/', views.get_expense_table_data, name='get_expense_table_data'),
    path('update-expenses/', views.update_expenses, name='update_expenses'),
]