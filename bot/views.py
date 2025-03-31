from django.conf import settings
import requests
from dotenv import load_dotenv
import os
from django.shortcuts import render, redirect
from bot.bot import bot
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import BotKnowledge, File, KeyWord, MyNumber
from .forms import BotSettingsForm

from django.http import JsonResponse
from django.shortcuts import render
from threading import Thread
from .bot import bot
from django.contrib.auth.decorators import login_required
import subprocess

load_dotenv()

GREENAPI_INSTANCE_ID = os.getenv('GREENAPI_INSTANCE_ID')
GREENAPI_API_TOKEN = os.getenv('GREENAPI_API_TOKEN')

@login_required
def status(request):
    status_url = f"https://7103.api.greenapi.com/waInstance{GREENAPI_INSTANCE_ID}/getWaSettings/{GREENAPI_API_TOKEN}"
    response = requests.get(status_url)
    
    if response.status_code == 200:
        data = response.json()
        
        return render(request, 'core/bot_status.html', {'status': data})
    else:
        return render(request, 'core/bot_status.html', {'error': 'Unable to fetch status'})

import pandas as pd

@login_required
def broadcast(request):
    from core.tasks import broadcast_task

    if request.method == "POST":
        text_message = request.POST.get("text_message", "")
        time_interval = int(request.POST.get("time_interval", 0))
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            return render(request, "core/broadcast.html", {"error": "Загрузите файл с номерами телефонов."})

        # Save the uploaded file to a temporary location
        file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
        with open(file_path, "wb") as f:
            for chunk in excel_file.chunks():
                f.write(chunk)

        # Pass file path to the task
        task = broadcast_task.delay(text_message, file_path, time_interval)

        return render(request, "core/broadcast_status.html", {
            "text_message": text_message,
            "phone_numbers": "Задача запущена, проверьте статус.",
            "task_id": task.id
        })

    return render(request, "core/broadcast.html")

def check_whatsapp_phones(phones):
    check_url = f"https://7103.api.greenapi.com/waInstance{GREENAPI_INSTANCE_ID}/checkWhatsapp/{GREENAPI_API_TOKEN}"
    filtered = []
    
    for phone in phones:
        print(phone)
        
        # Используем просто словарь, без json.dumps()
        payload = {"phoneNumber": int(phone)}
        
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(check_url, json=payload, headers=headers)
        print(response.text)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("existsWhatsapp", False):
                filtered.append(f"{phone}@c.us")
    
    return filtered



bot_thread = None
bot_running = bot.running

@login_required
def run_bot(request):
    """
    Start the WhatsApp bot.
    """
    global bot_thread, bot_running

    if bot_running:
        return JsonResponse({"status": "error", "message": "Bot is already running."}, status=400)

    def bot_runner():
        try:
            bot.run()  # Call the bot's run method
        except Exception as e:
            print(f"Bot encountered an error: {e}")

    # Start the bot in a new thread
    bot_thread = Thread(target=bot_runner, daemon=True)
    bot_thread.start()
    bot_running = True
    return JsonResponse({"status": "success", "message": "Bot started successfully."})


@login_required
def stop_bot(request):
    """
    Stop the WhatsApp bot.
    """
    global bot_thread, bot_running

    if not bot_running:
        return JsonResponse({"status": "error", "message": "Bot is not running."}, status=400)

    # To stop the bot, you might need to implement a stop mechanism in the bot class
    bot_running = False
    bot_thread = None
    return JsonResponse({"status": "success", "message": "Bot stopped successfully."})

@login_required
def bot_status(request):
    """
    Get the current status of the bot.
    """
    global bot_running

    return JsonResponse({"status": "running" if bot_running else "stopped"})

@login_required
def bot_settings(request):
    # Get or create bot knowledge instance
    bot_knowledge = BotKnowledge.load()
    form = BotSettingsForm(instance=bot_knowledge)  # Ensure `form` is always initialized

    if request.method == 'POST':
        if 'save' in request.POST:
            # Handle bot settings form
            form = BotSettingsForm(request.POST, instance=bot_knowledge)
            if form.is_valid():
                form.save()
                messages.success(request, 'Настройки бота успешно обновлены')
                return redirect('bot_settings')
        
        elif 'upload_file' in request.POST:
            # Handle file upload
            filename = request.POST.get('filename')
            file = request.FILES.get('file')
            if file:
                new_file = File(
                    filename=filename or file.name,
                    file=file,
                    knowledge=bot_knowledge
                )
                new_file.save()
                messages.success(request, 'Файл успешно загружен')
                return redirect('bot_settings')
        
        elif 'delete_file' in request.POST:
            # Handle file deletion
            file_id = request.POST.get('file_id')
            try:
                file = File.objects.get(id=file_id)
                file.delete()
                messages.success(request, 'Файл успешно удален')
            except File.DoesNotExist:
                messages.error(request, 'Файл не найден')
            return redirect('bot_settings')
        
        elif 'add_keyword' in request.POST:
            # Handle keyword addition
            word = request.POST.get('keyword')
            if word:
                KeyWord.objects.create(word=word)
                messages.success(request, 'Ключевое слово добавлено')
            return redirect('bot_settings')

        elif 'delete_keyword' in request.POST:
            # Handle keyword deletion
            keyword_id = request.POST.get('keyword_id')
            if KeyWord.objects.filter(id=keyword_id).exists():
                KeyWord.objects.filter(id=keyword_id).delete()
                messages.success(request, 'Ключевое слово удалено')
            else:
                messages.error(request, 'Ключевое слово не найдено')
            return redirect('bot_settings')
        
        elif 'add_number' in request.POST:
            # Handle phone number addition
            number = request.POST.get('number')
            if number:
                MyNumber.objects.create(number=number)
                messages.success(request, 'Номер телефона добавлен')
            return redirect('bot_settings')

        elif 'delete_number' in request.POST:
            # Handle phone number deletion
            number_id = request.POST.get('number_id')
            if MyNumber.objects.filter(id=number_id).exists():
                MyNumber.objects.filter(id=number_id).delete()
                messages.success(request, 'Номер телефона удален')
            else:
                messages.error(request, 'Номер телефона не найден')
            return redirect('bot_settings')

    files = File.objects.filter(knowledge=bot_knowledge).order_by('-created_at')

    return render(request, 'core/bot_settings.html', {
        'form': form,
        'files': files,
        'keywords': KeyWord.objects.all(),
        'numbers': MyNumber.objects.all()
    })

@login_required
def restart_gunicorn(request):
    if request.method == "POST":
        try:
            subprocess.run(["sudo", "systemctl", "restart", "gunicorn"], check=True)
            return JsonResponse({"message": "Gunicorn успешно перезапущен."})
        except subprocess.CalledProcessError as e:
            return JsonResponse({"message": f"Ошибка при перезапуске Gunicorn: {e}"}, status=500)
    return JsonResponse({"message": "Неверный метод запроса."}, status=400)