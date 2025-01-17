import time
import openai
from os.path import join
import requests
import json
from dotenv import load_dotenv

from openai import OpenAI





class WhatsappBot:
    
    def __init__(self, instance_id: str, api_token: str, openai_api_key: str, storage_id: str):
        from bot.models import BotKnowledge
        self.instance_id = instance_id
        self.api_token = api_token
        self.openai_api_key = openai_api_key
        self.running = False
        self.storage_id = storage_id

        self.send_message_url = f"https://7103.api.greenapi.com/waInstance{instance_id}/sendMessage/{api_token}"
        self.receive_message_url = f"https://7103.api.greenapi.com/waInstance{instance_id}/receiveNotification/{api_token}?receiveTimeout=5"
        self.delete_message_url = f"https://7103.api.greenapi.com/waInstance{instance_id}/deleteNotification/{api_token}/"
        self.send_location_url = f"https://7103.api.greenapi.com/waInstance{instance_id}/sendLocation/{api_token}"
        self.send_file_by_upload_url = f"https://7103.api.greenapi.com/waInstance{instance_id}/sendFileByUpload/{api_token}"

        self.openai_client = OpenAI(api_key=openai_api_key)
        knowledge = BotKnowledge.load()
        if knowledge:
            title = knowledge.title
            content = knowledge.content
        self.assistant = self.openai_client.beta.assistants.create(
            name=title,
            instructions=content,
            model="gpt-4-turbo-preview",
            tools=[
                {
                    "type": "file_search",
                }
            ],
            tool_resources={
                "file_search": {"vector_store_ids": [storage_id]}
            },
        )
        self.user_threads = {}
        self.handlers = {}

    def get_or_create_thread(self, chat_id: str) -> str:
        """Получает существующий или создает новый thread для пользователя"""
        if chat_id not in self.user_threads:
            thread = self.openai_client.beta.threads.create()
            self.user_threads[chat_id] = thread.id
        return self.user_threads[chat_id]

    def send_message(self, message: str, chat_id: str):
        payload = {
            "chatId": chat_id,
            "message": message
        }
        headers = {
            'Content-Type': 'application/json'
        }
        requests.post(self.send_message_url, headers=headers, data=json.dumps(payload))

    def broadcast_message(self, message: str, chat_ids: list, sleep_time: int):
        """
        Отправляет сообщение списку номеров.
        
        :param message: Сообщение, которое нужно отправить.
        :param chat_ids: Список номеров (chatId), например, ['77712345678@c.us', ...].
        """
        print(f"Отправка сообщения: {message}")
        print(f"Количество получателей: {len(chat_ids)}")
        print(f"Интервал между сообщениями: {sleep_time} сек.")
        for chat_id in chat_ids:
            try:
                self.send_message(message, chat_id)
                print(f"Сообщение отправлено: {chat_id}")
                if len(chat_ids) > 1:
                    time.sleep(sleep_time)
            except Exception as e:
                print(f"Ошибка при отправке на {chat_id}: {e}")

    def send_location(self, chat_id: str):
        payload = {
            "chatId": chat_id,
            "latitude": 12.3456789,
            "longitude": 10.1112131,
            "nameLocation": 'Restaurant',
            "address": "123456, Perm",
        }
        headers = {
            'Content-Type': 'application/json'
        }

        requests.post(self.send_location_url, headers=headers, data=json.dumps(payload))

    def check_new_messages(self):
        try:
            response = requests.get(self.receive_message_url)
            
            # Проверяем статус ответа
            if response.status_code != 200:
                print(f"Ошибка API: статус {response.status_code}")
                return None
                
            # Проверяем, не пустой ли ответ
            if not response.text or response.text.isspace():
                return None
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                print("Получен пустой ответ или неверный формат JSON")
                return None
                
            if data is not None:
                rec_id = data.get('receiptId')
                if rec_id:
                    delete_response = requests.delete(f'{self.delete_message_url}/{rec_id}')
                    if delete_response.status_code != 200:
                        print(f"Ошибка при удалении уведомления: {delete_response.status_code}")

                if data.get('body', {}).get('senderData') and data.get('body', {}).get('messageData'):
                    return data
                    
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при получении сообщений: {e}")
            return None

    def register_handler(self, trigger: str):

        def decorator(func):
            self.handlers[trigger.lower()] = func
            return func

        return decorator
    def download_voice_message(self, voice_url: str) -> bytes:
        """
        Загружает голосовое сообщение с указанного URL.
        
        :param voice_url: URL голосового сообщения.
        :return: Байтовые данные файла.
        """
        response = requests.get(voice_url)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Ошибка загрузки голосового сообщения: {response.status_code}")
            return None

    def transcribe_voice_message(self, audio_data: bytes) -> str:
        """
        Распознает текст из голосового сообщения с помощью Whisper API.
        
        :param audio_data: Байтовые данные голосового сообщения.
        :return: Распознанный текст.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
            }
            files = {
                "file": ("audio.ogg", audio_data, "audio/ogg"),
                "model": (None, "whisper-1")
            }
            response = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files)
            if response.status_code == 200:
                return response.json().get("text", "Не удалось распознать текст.")
            else:
                print(f"Ошибка Whisper API: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при распознавании."
        except Exception as e:
            print(f"Ошибка: {e}")
            return "Извините, произошла ошибка при обработке голосового сообщения."
            
    def process_message(self, message_data: dict):
        body = message_data.get('body')
        msg_type = body.get('typeWebhook')
        if msg_type == 'incomingMessageReceived':
            sender_data = body.get('senderData')
            message_data = body.get('messageData')

            chat_id = sender_data.get('chatId')
            message_type = message_data.get('typeMessage')

            if message_type == 'audioMessage':
                file_data = message_data.get('fileMessageData')
                if file_data:
                    download_url = file_data.get('downloadUrl')
                    if download_url:
                        audio_data = self.download_voice_message(download_url)
                        if audio_data:
                            transcribed_text = self.transcribe_voice_message(audio_data)
                            openai_response = self.ask_openai(transcribed_text, chat_id)  # Добавляем chat_id
                            if openai_response:
                                self.send_message(openai_response, chat_id)
                            else:
                                self.send_message("Извините, не могу обработать запрос.", chat_id)

            text_message = message_data.get('textMessageData', {}).get('textMessage')
            if text_message:
                trigger = text_message.lower()
                if self.handlers.get(trigger):
                    trigger_func = self.handlers[trigger]
                    trigger_func(chat_id)
                    return

                openai_response = self.ask_openai(text_message, chat_id)  # Добавляем chat_id
                if openai_response:
                    self.send_message(openai_response, chat_id)
                else:
                    self.send_message("Извините, не могу обработать запрос.", chat_id)

    def ask_openai(self, prompt: str, chat_id: str) -> str:
        try:
            thread_id = self.get_or_create_thread(chat_id)
            
            self.openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant.id
            )
            
            while True:
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run.status == 'completed':
                    break
                elif run.status == 'failed':
                    return "Извините, произошла ошибка при обработке вашего запроса."
                time.sleep(1)
            
            messages = self.openai_client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            return messages.data[0].content[0].text.value

        except Exception as e:
            print(f"Ошибка OpenAI Assistant: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."

    def run(self, polling_interval: int = 1):
        self.running = True
        print("Запуск...")
        try:
            while self.running:
                data = self.check_new_messages()

                if data is not None:
                    self.process_message(data)

                time.sleep(polling_interval)
        except KeyboardInterrupt:
            print("Бот отключен.")

    def stop(self):
        self.running = False


    def add_file(self, file):
        from bot.models import File
        store_id = self.storage_id

        file_object = self.openai_client.files.create(file=(file.filename, file.file), purpose="assistants")
        self.openai_client.beta.vector_stores.files.create(
            vector_store_id=store_id, file_id=file_object.id
        )
        return file_object.id

    def update_file(self, file):
        store_id = self.storage_id
        self.openai_client.beta.vector_stores.files.delete(
            vector_store_id=store_id, file_id=file.object_id
        )
        file_object = self.openai_client.files.create(file=(file.filename, file.file), purpose="assistants")
        self.openai_client.beta.vector_stores.files.create(
            vector_store_id=store_id, file_id=file_object.id
        )
        return file_object.id

    def delete_file(self, file):
        store_id = self.storage_id
        self.openai_client.beta.vector_stores.files.delete(
            vector_store_id=store_id, file_id=file.object_id
        )
