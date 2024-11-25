from django.urls import path
from . import views

urlpatterns = [
    path('', views.income, name='income'),
]