from django.urls import path

from bot import views

urlpatterns = [
    path('status', views.status, name='bot_status'),
    path('broadcast', views.broadcast, name='run_broadcast'),
    path('run_bot', views.run_bot, name='start_bot'),
    path('stop_bot', views.stop_bot, name='stop_bot'),
    path('status_bot', views.bot_status, name='status_bot'),
    path('settings', views.bot_settings, name='bot_settings'),
]
