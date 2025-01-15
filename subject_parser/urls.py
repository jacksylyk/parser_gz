from django.urls import path, include

from core.views import fetch_customers_view, task_list_view, export_phone_numbers_to_excel
from subject_parser.views import customers_without_phone

urlpatterns = [
    path('list', fetch_customers_view, name='list'),
    path('search_phones', customers_without_phone, name='search_phones'),
    path('task_list_view', task_list_view, name='task_status_page'),
    path('export', export_phone_numbers_to_excel, name='export')
]
