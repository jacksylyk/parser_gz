from django.contrib import admin
from bot.models import BotKnowledge, File


@admin.register(BotKnowledge)
class BotKnowledgeAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not BotKnowledge.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass