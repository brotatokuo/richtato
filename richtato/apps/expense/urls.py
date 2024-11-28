from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense, name='expense'),
    path('add-expense-entry/', views.add_expense_entry, name='add_expense_entry'),
]