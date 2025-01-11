from django.shortcuts import render
import requests
from django.shortcuts import render
from django.http import JsonResponse

from subject_parser.models import Customer

from bs4 import BeautifulSoup

# from core.models import Customer


from django.core.paginator import Paginator

def index(request):
    customers = Customer.objects.all()

    paginator = Paginator(customers, 25)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'parser/main.html', {'customers': page_obj})



# URL и токен для доступа к GraphQL API
GRAPHQL_API_URL = "https://ows.goszakup.gov.kz/v3/graphql"
GRAPHQL_API_TOKEN = "2d9be756545e4447462a55fbe2ec0ff0"

BASE_URL = "https://goszakup.gov.kz"


def fetch_customers(request):
    total_saved = 0
    page_url = f"{BASE_URL}/ru/registry/supplierreg?filter%5Btype%5D%5B0%5D=1&count_record=50"

    while page_url:
        response = requests.get(page_url)
        if response.status_code != 200:
            return JsonResponse({"error": f"Failed to fetch page: {page_url}"}, status=response.status_code)

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", id="search-result")
        if not table:
            break

        rows = table.find_all("tr")
        customers_to_save = []

        for row in rows:
            tds = row.find_all("td")[:3]
            if len(tds) < 3:
                continue

            customer_number = tds[0].text.strip()
            customer_name = tds[1].text.strip()
            bin_value = tds[2].text.strip()

            if bin_value:
                # Проверяем, существует ли уже заказчик с таким БИН
                existing_customer = Customer.objects.filter(bin=bin_value).first()
                if not existing_customer:
                    customers_to_save.append(Customer(
                        customer_number=customer_number,
                        customer_name=customer_name,
                        bin=bin_value
                    ))

        # Используем bulk_create для добавления заказчиков
        if customers_to_save:
            Customer.objects.bulk_create(customers_to_save, ignore_conflicts=True)
            total_saved += len(customers_to_save)

        pagination = soup.find("ul", class_="pagination")
        if not pagination:
            break

        next_button = pagination.find("a", href=True)
        if next_button:
            span = next_button.find("span")
            if span and span.text.strip() == "»":
                page_url = BASE_URL + next_button["href"]

    return JsonResponse({"message": f"Total customers saved: {total_saved}"})