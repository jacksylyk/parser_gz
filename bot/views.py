import requests
from dotenv import load_dotenv
import os
from django.shortcuts import render, redirect
from bot.bot import bot

load_dotenv()

GREENAPI_INSTANCE_ID = os.getenv('GREENAPI_INSTANCE_ID')
GREENAPI_API_TOKEN = os.getenv('GREENAPI_API_TOKEN')

def status(request):
    status_url = f"https://7103.api.greenapi.com/waInstance{GREENAPI_INSTANCE_ID}/getWaSettings/{GREENAPI_API_TOKEN}"
    response = requests.get(status_url)
    print(response.json)
    
    if response.status_code == 200:
        data = response.json()
        
        return render(request, 'core/bot_status.html', {'status': data})
    else:
        return render(request, 'core/bot_status.html', {'error': 'Unable to fetch status'})

import pandas as pd

def broadcast(request):
    if request.method == "POST":
        text_message = request.POST.get("text_message", "")
        time_interval = int(request.POST.get("time_interval", 0))

        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            return render(request, "core/broadcast.html", {"error": "Загрузите файл с номерами телефонов."})

        try:
            df = pd.read_excel(excel_file)
            phone_numbers = df.iloc[:, 0].dropna().tolist()
            checked_numbers = check_whatsapp_phones(phone_numbers)
            bot.broadcast_message(text_message, checked_numbers, time_interval)
        except Exception as e:
            return render(request, "core/broadcast.html", {"error": f"Ошибка при чтении файла: {e}"})

        return render(request, "core/broadcast_status.html", {
            "text_message": text_message,
            "phone_numbers": len(phone_numbers),
            "time_interval": time_interval
        })

    return render(request, "core/broadcast.html")

import json

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


from django.http import JsonResponse
from django.shortcuts import render
from threading import Thread
from .bot import bot

bot_thread = None
bot_running = False

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


def bot_status(request):
    """
    Get the current status of the bot.
    """
    global bot_running

    return JsonResponse({"status": "running" if bot_running else "stopped"})