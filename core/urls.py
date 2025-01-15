from django.urls import path

from core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('task_status/<str:task_id>/', views.task_status_view, name='task_status'),
]
