import requests
from django.core.files import File
from io import BytesIO
from .models import Contract, PhoneNumber

GRAPHQL_API_URL = "https://ows.goszakup.gov.kz/v3/graphql"
GRAPHQL_API_TOKEN = "2d9be756545e4447462a55fbe2ec0ff0"

def load_contract(customer):
    bin_number = customer.bin

    query = """
    query Contract {
        Contract(
            filter: { customerBin: "%s", refContractTypeId: 1 }
            limit: 1
        ) {
            id
            File {
                id
                filePath
                originalName
                nameRu
                nameKz
                indexDate
                systemId
            }
        }
    }
    """ % bin_number

    url = GRAPHQL_API_URL  # Замените на URL вашего GraphQL API
    headers = {"Authorization": f"Bearer {GRAPHQL_API_TOKEN}"}  # Если требуется авторизация
    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        file_info = data.get('data', {}).get('Contract', [{}])[0].get('File', {})

        if file_info:
            file_url = file_info.get('filePath')
            original_name = file_info.get('originalName')

            # Скачиваем файл
            file_response = requests.get(file_url)

            if file_response.status_code == 200:
                # Создаем объект Contract и сохраняем файл
                contract = Contract(
                    file_url=file_url,
                    customer=customer
                )

                contract.file_path.save(original_name, File(BytesIO(file_response.content)))
                contract.save()

                print("Файл успешно загружен и объект добавлен в базу данных.")
            else:
                print("Не удалось скачать файл.")
        else:
            print("Не найден файл для указанного заказчика.")
    else:
        print("Ошибка при выполнении GraphQL запроса:", response.status_code)

import pdfplumber


def read_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_text = []

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    page_words = []
                    lines = page_text.strip().split('\n')
                    for line in lines:
                        words = line.split()
                        page_words.extend(words)
                    
                    pages_text.extend(page_words)

            return pages_text

    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def search_phone_numbers(customer):
    print(customer.bin)
    contract = Contract.objects.filter(customer=customer).first()
    if not contract:
        load_contract(customer)
        contract = Contract.objects.filter(customer=customer).first()
    file_path = contract.file_path

    data = extract_text_near_word(file_path)

    if data:
        for number in data:
            PhoneNumber.objects.create(number=number, customer=customer)
            
def extract_text_near_word(file_path):
    phone_numbers = []
    search_word = "Юридические адреса и банковские реквизиты Сторон"
    search_word2 = "Реквизиты Сторон"

    try:
        with pdfplumber.open(file_path) as pdf:
            # Перебираем страницы
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and search_word in text:
                    print(f"Page {page_num} contains the word '{search_word}':")

                    # Разделение текста на строки
                    lines = text.split('\n')
                    found_phone = False

                    for line in lines:
                        if search_word in line:
                            print(f"Found '{search_word}' in: {line}")

                    # Извлекаем текст только из левой колонки
                    left_bbox = (0, 0, page.width / 2, page.height)
                    left_text = page.within_bbox(left_bbox).extract_text()
                    need_data = left_text.split('\n')

                    for i in need_data:
                        if 'Тел.:' in i:
                            # Извлекаем телефонные номера и очищаем их
                            phone_numbers.extend(i.replace('Тел.:', '').split(','))
                            found_phone = True

                    # Если не найдено телефонных номеров, проверяем следующую страницу
                    if not found_phone and page_num < len(pdf.pages):
                        next_page = pdf.pages[page_num]
                        next_left_bbox = (0, 0, next_page.width / 2, next_page.height)
                        next_left_text = next_page.within_bbox(next_left_bbox).extract_text()
                        next_need_data = next_left_text.split('\n')

                        for i in next_need_data:
                            if 'Тел.:' in i:
                                # Извлекаем телефонные номера и очищаем их
                                phone_numbers.extend(i.replace('Тел.:', '').split(','))
                
                elif text and search_word2 in text:
                    print(f"Page {page_num} contains the word '{search_word2}':")

                    # Разделение текста на строки
                    lines = text.split('\n')
                    found_phone = False

                    for line in lines:
                        if search_word2 in line:
                            print(f"Found '{search_word2}' in: {line}")

                    # Извлекаем текст только из левой колонки
                    left_bbox = (0, 0, page.width / 2, page.height)
                    left_text = page.within_bbox(left_bbox).extract_text()
                    need_data = left_text.split('\n')

                    for i in need_data:
                        if 'Тел.:' in i:
                            # Извлекаем телефонные номера и очищаем их
                            phone_numbers.extend(i.replace('Тел.:', '').split(','))
                            found_phone = True

                    # Если не найдено телефонных номеров, проверяем следующую страницу
                    if not found_phone and page_num < len(pdf.pages):
                        next_page = pdf.pages[page_num]
                        next_left_bbox = (0, 0, next_page.width / 2, next_page.height)
                        next_left_text = next_page.within_bbox(next_left_bbox).extract_text()
                        next_need_data = next_left_text.split('\n')

                        for i in next_need_data:
                            if 'Тел.:' in i:
                                # Извлекаем телефонные номера и очищаем их
                                phone_numbers.extend(i.replace('Тел.:', '').split(','))

        # Очищаем номера телефонов от лишних пробелов
        phone_numbers = [phone_number.strip() for phone_number in phone_numbers]
        print(phone_numbers)
        return phone_numbers

    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return []
    