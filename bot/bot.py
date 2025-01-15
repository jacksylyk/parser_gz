from django.conf import settings
from .functions import WhatsappBot
from dotenv import load_dotenv
import os

load_dotenv()

GREENAPI_INSTANCE_ID = os.getenv('GREENAPI_INSTANCE_ID')
GREENAPI_API_TOKEN = os.getenv('GREENAPI_API_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

bot = WhatsappBot(
    GREENAPI_INSTANCE_ID,
    GREENAPI_API_TOKEN,
    OPENAI_API_KEY
)