from django.urls import path

from bot import views

urlpatterns = [
    path('status', views.status, name='bot_status'),
    path('broadcast', views.broadcast, name='run_broadcast'),
]
