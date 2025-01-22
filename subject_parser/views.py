from django.shortcuts import redirect
from core.tasks import parse_phones
from django.contrib.auth.decorators import login_required

@login_required
def customers_without_phone(request):
    parse_phones.delay()
    return redirect('index')