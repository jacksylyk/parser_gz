from django.conf import settings
from .functions import WhatsappBot
from dotenv import load_dotenv
import os

load_dotenv()

class BotInstance:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                GREENAPI_INSTANCE_ID = os.getenv('GREENAPI_INSTANCE_ID')
                GREENAPI_API_TOKEN = os.getenv('GREENAPI_API_TOKEN')
                OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
                STORAGE_ID = os.getenv('STORAGE_ID')

                if not all([GREENAPI_INSTANCE_ID, GREENAPI_API_TOKEN, OPENAI_API_KEY, STORAGE_ID]):
                    raise ValueError("Missing required environment variables for WhatsApp Bot.")

                cls._instance = WhatsappBot(
                    GREENAPI_INSTANCE_ID,
                    GREENAPI_API_TOKEN,
                    OPENAI_API_KEY,
                    STORAGE_ID
                )
            except Exception as e:
                raise RuntimeError(f"Error initializing bot: {e}")
        return cls._instance

bot = BotInstance.get_instance()