import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django_celery_results.models import TaskResult
from core.tasks import fetch_and_save_customers
from subject_parser.models import Customer
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from celery.result import AsyncResult

from bs4 import BeautifulSoup

from django.core.paginator import Paginator
import os
from dotenv import load_dotenv

load_dotenv()

@login_required
def index(request):
    customers = Customer.objects.all()

    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    customers_with_phone_numbers = []
    for customer in page_obj:
        phone_numbers = customer.phone_numbers.all()
        customers_with_phone_numbers.append({
            'customer': customer,
            'phone_numbers': phone_numbers
        })

    return render(request, 'parser/main.html', {'data': customers_with_phone_numbers, 'page_obj': page_obj})

@login_required
def fetch_customers_view(request):
    task = fetch_and_save_customers.delay()
    return redirect('task_status_page')

@login_required
def task_status_view(request, task_id):
    result = AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "task_name": result.task_name if hasattr(result, 'task_name') else "Неизвестно",
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
    return JsonResponse(response)

@login_required
def task_list_view(request):
    tasks = TaskResult.objects.all().order_by('-date_done')[:50]
    return render(request, 'core/results.html', {'tasks': tasks})


import openpyxl
from openpyxl.styles import Font
from django.http import HttpResponse
from subject_parser.models import PhoneNumber


@login_required
def export_phone_numbers_to_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Phone Numbers"

    headers = ["ID", "Phone Number", "Customer"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)

    phone_numbers = PhoneNumber.objects.select_related('customer').all()

    for row_num, phone_number in enumerate(phone_numbers, 2):
        ws.cell(row=row_num, column=1, value=phone_number.id)
        ws.cell(row=row_num, column=2, value=phone_number.number)
        ws.cell(row=row_num, column=3, value=str(phone_number.customer.customer_name))

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="phone_numbers.xlsx"'

    wb.save(response)

    return response
