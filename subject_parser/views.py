from django.shortcuts import render, redirect
from .models import Customer
from .utils import search_phone_numbers

def customers_without_phone(request):
    customers = Customer.objects.filter(phone_numbers__isnull=True)
    for customer in customers:
        search_phone_numbers(customer)
    return redirect('index')