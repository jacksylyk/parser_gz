# parser_gz

Django-проект для работы с реестром госзакупок Казахстана ([goszakup.gov.kz](https://goszakup.gov.kz)):

1. **Парсер заказчиков** — собирает список участников (название, номер, БИН) из реестра.
2. **Поиск телефонов** — по БИН через GraphQL API госзакупок скачивает договор заказчика (PDF) и вытаскивает из него номера телефонов.
3. **WhatsApp-рассылка** — проверяет, зарегистрированы ли номера в WhatsApp, и делает массовую рассылку с заданным интервалом.
4. **WhatsApp-бот на OpenAI** — отвечает клиентам, используя загружаемые файлы базы знаний (Green API + OpenAI Assistants / vector store).

Долгие операции выполняются в фоне через Celery.

## Стек

- Python 3.10+, Django 5.1
- Celery 5.4 + Redis (брокер), `django-celery-results` (результаты в БД)
- PostgreSQL
- BeautifulSoup, pdfplumber, pandas / openpyxl
- OpenAI API, [Green API](https://green-api.com) (WhatsApp)

## Структура

| Приложение | Назначение |
|---|---|
| `core` | Главная страница, Celery-задачи (парсинг заказчиков, поиск телефонов, рассылка), статусы задач, экспорт в Excel |
| `subject_parser` | Модели `Customer`, `Contract`, `PhoneNumber`; загрузка договоров и поиск номеров в PDF (`utils.py`) |
| `bot` | WhatsApp-бот, настройки бота и база знаний, рассылка, модели `Chat` / `Message` |
| `parser_gz` | Настройки проекта, конфигурация Celery |
| `templates` | HTML-шаблоны |

## Установка

```bash
git clone <url-репозитория>
cd parser_gz

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
```

### Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

| Переменная | Описание |
|---|---|
| `GRAPHQL_API_URL` | URL GraphQL API госзакупок (`https://ows.goszakup.gov.kz/v3/graphql`) |
| `GRAPHQL_API_TOKEN` | Токен доступа к API госзакупок |
| `BASE_URL` | `https://goszakup.gov.kz` |
| `GREENAPI_INSTANCE_ID` | ID инстанса Green API |
| `GREENAPI_API_TOKEN` | Токен Green API |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `STORAGE_ID` | ID векторного хранилища OpenAI для базы знаний бота |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Настройки Django |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Подключение к PostgreSQL |
| `CELERY_BROKER_URL` | Адрес Redis (по умолчанию `redis://127.0.0.1:6379/0`) |

> Модуль `bot.bot` создаёт бота при импорте и падает, если не заданы все четыре переменные бота — заполните их даже для запуска одного только парсера.

### База данных и Redis

Параметры PostgreSQL (`DB_*`) и брокера Celery (`CELERY_BROKER_URL`) берутся из `.env`. Создайте БД и пользователя под эти настройки и запустите Redis.

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Запуск

Каждая команда — в отдельном терминале:

```bash
# веб-приложение
python manage.py runserver

# Celery-воркер
celery -A parser_gz worker -l info
# на Windows добавьте: --pool=solo

# WhatsApp-бот
python manage.py run_bot
```

## Использование

Все страницы, кроме логина, требуют авторизации (`/accounts/login/`).

| URL | Что делает |
|---|---|
| `/` | Главная |
| `/list` | Запуск парсинга списка заказчиков |
| `/parser/search_phones` | Запуск поиска телефонов для заказчиков без номеров |
| `/task_list_view` | Список и статусы задач |
| `/export` | Выгрузка найденных номеров в Excel |
| `/bot/broadcast` | Рассылка по номерам из Excel-файла (первый столбец) |
| `/bot/status`, `/bot/status_bot` | Статус рассылки и бота |
| `/bot/run_bot`, `/bot/stop_bot` | Старт / остановка бота |
| `/bot/settings` | Инструкции ассистента и файлы базы знаний |
| `/admin/` | Админ-панель |

## Продакшен

В `.env` задайте уникальный `SECRET_KEY`, `DEBUG=False`, свой `ALLOWED_HOSTS` и надёжный `DB_PASSWORD`. Запускайте через `gunicorn parser_gz.wsgi`.

## Замечания

Используйте парсер и рассылку в соответствии с законодательством, правилами сайта госзакупок и условиями WhatsApp: массовая рассылка без согласия получателей может привести к блокировке номера.
