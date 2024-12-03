from django.urls import path
from . import views

page_name = 'budget'
urlpatterns = [
    path('', views.main, name=page_name),
    # path('get-budeget-months/', views.get_budget_months, name='get_budget_months'),
    path('get-plot-data/<int:year>/<str:month>', views.get_plot_data, name=f'{page_name}_get_plot_data'),
]