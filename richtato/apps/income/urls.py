from django.urls import path
from . import views

urlpatterns = [
    path('', views.income, name='income'),
    path('add-earning-entry/', views.add_earning_entry, name='add_earning_entry'),
]