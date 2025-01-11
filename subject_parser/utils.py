import requests
from django.core.files import File
from io import BytesIO
from .models import Contract


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
