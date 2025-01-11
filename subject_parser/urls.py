from django.urls import path, include

from core import views

urlpatterns = [
    path('list', views.fetch_customers, name='list'),
]
