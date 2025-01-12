from django.urls import path, include

from core.views import fetch_customers
from subject_parser.views import customers_without_phone

urlpatterns = [
    path('list', fetch_customers, name='list'),
    path('search_phones', customers_without_phone, name='search_phones'),
]
