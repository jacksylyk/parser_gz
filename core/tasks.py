from celery import shared_task
from bs4 import BeautifulSoup
import requests
from subject_parser.models import Customer
import os
from subject_parser.utils import search_phone_numbers


@shared_task(name="parse_customers")
def fetch_and_save_customers():
    BASE_URL = os.getenv('BASE_URL')
    total_saved = 0
    base_url = f"{BASE_URL}/ru/registry/supplierreg?filter%5Btype%5D%5B0%5D=1&count_record=50"
    page = 1
    page_url = f"{base_url}&page={page}"

    while True:
        response = requests.get(page_url)
        if response.status_code != 200:
            break

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
                existing_customer = Customer.objects.filter(bin=bin_value).exists()
                if not existing_customer:
                    customers_to_save.append(Customer(
                        customer_number=customer_number,
                        customer_name=customer_name,
                        bin=bin_value
                    ))

        if customers_to_save:
            Customer.objects.bulk_create(customers_to_save, ignore_conflicts=True)
            total_saved += len(customers_to_save)

        page += 1
        page_url = f"{base_url}&page={page}"

    return {"total_saved": total_saved}

@shared_task(name="parse_phones_task")
def parse_phones():
    customers = Customer.objects.filter(phone_numbers__isnull=True)
    for customer in customers:
        search_phone_numbers(customer)
    
    return {"message": "Phone numbers search task completed."}

from bot.views import check_whatsapp_phones
import pandas as pd
from bot.bot import bot

@shared_task
def broadcast_task(text_message, file_path, time_interval):
    df = pd.read_excel(file_path)
    phone_numbers = df.iloc[:, 0].dropna().tolist()
    checked_numbers = check_whatsapp_phones(phone_numbers)

    bot.broadcast_message(text_message, checked_numbers, time_interval)
    return f"Sended messages: {len(checked_numbers)}"