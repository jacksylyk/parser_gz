from django.shortcuts import redirect
from core.tasks import parse_phones

def customers_without_phone(request):
    parse_phones.delay()
    return redirect('index')