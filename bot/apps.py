from django.apps import AppConfig
import threading


class BotAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot"

    def ready(self):
        from .bot import bot
        print(type(bot))
        if not getattr(self, '_bot_thread_started', False):
            self._bot_thread_started = True
            thread = threading.Thread(target=bot.run, daemon=True)
            thread.start()