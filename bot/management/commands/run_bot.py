from django.core.management.base import BaseCommand
from bot.bot import bot

class Command(BaseCommand):
    help = "Run the WhatsApp bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting WhatsApp bot...")
        bot.run()