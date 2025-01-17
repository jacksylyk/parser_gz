from django.db import models
import os 

class BotKnowledge(models.Model):
    title = models.CharField(max_length=255, verbose_name='Имя ассистента')
    content = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Настройки бота'
        verbose_name_plural = 'Настройки бота'

    def save(self, *args, **kwargs):
        if not self.pk and BotKnowledge.objects.exists():
            # If trying to create a new object when one already exists
            raise ValueError('Может существовать только один экземпляр BotKnowledge')
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(
            defaults={
                'title': 'Default Assistant Name',
                'content': 'Default Assistant Instructions'
            }
        )
        return obj

    def __str__(self):
        return self.title

class File(models.Model):
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='knowledge_files/')
    object_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    knowledge = models.ForeignKey(BotKnowledge, on_delete=models.CASCADE, related_name='files')
    
    _is_saving = False  # Prevent infinite recursion

    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if self._is_saving:
            return  # Prevent recursion
        
        self._is_saving = True
        file_extension = f".{self.file.name.split('.')[-1]}"
        
        if not self.filename:
            self.filename = os.path.basename(self.file.name)
        else:
            self.filename = f"{self.filename}{file_extension}"

        

        # Update knowledge base after saving
        from bot.bot import bot
        object_id = bot.add_file(self)
        self.object_id = object_id
        self._is_saving = False
        super().save(*args, **kwargs)

    def update(self, *args, **kwargs):
        from bot.bot import bot
        
        object_id = bot.update_file(self)
        self.object_id = object_id
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from bot.bot import bot
        bot.delete_file(self)
        super().delete(*args, **kwargs)


    class Meta:
        verbose_name = 'Файл знаний'
        verbose_name_plural = 'Файлы знаний'