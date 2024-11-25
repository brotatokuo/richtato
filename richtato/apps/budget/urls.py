from django.urls import path
from . import views

urlpatterns = [
    path('', views.budget, name='budget'),
    path('get-budeget-months/', views.get_budget_months, name='get_budget_months'),
    path('plot-budget-data/', views.plot_budget_data, name='plot_budget_data'),
]