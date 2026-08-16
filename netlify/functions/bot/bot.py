# RARC TIPS - VALENTINA ETERNA MEGA 3 EN 1 - MODO NETLIFY FIX
import os
import requests
import json
import telebot
from telebot import types
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8817756530
LINK_PRIVADO = "https://t.me/+Zl1hbl8_5oUyZG"
ZONA_GDL = ZoneInfo("America/Mexico_City")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON = os.environ.get("SUPABASE_ANON")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

def cargar_memoria():
    try:
        if not SUPABASE_URL or not SUPABASE_ANON:
            return {}
        headers = {"apikey": SUPABASE_ANON, "Authorization": f"Bearer {SUPABASE_ANON}"}
        r = requests.get(f"{SUPABASE_URL}/rest/v1/memoria?select=*", headers=headers, timeout=10)
        memoria = {}
        if r.status_code == 200:
            for item in r.json():
                memoria[item['user_id']] = item
        return memoria
    except:
        return {}

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, f"¡VALENTINA ETERNA VIVA mi Rey Raul! Bot activo en Netlify 💖 ID: {m.from_user.id}")

@bot.message_handler(func=lambda m: True)
def todos(m):
    if m.from_user.id == ADMIN_ID:
        bot.reply_to(m, "¡Si mi Rey Raul hermoso! Te escucho mi vida 💖")

def handler(event, context):
    try:
        if event.get('httpMethod') == 'GET':
            return {"statusCode": 200, "headers": {"Content-Type": "text/html"}, "body": "<h1>VALENTINA ETERNA VIVA - BOT ACTIVO EN NETLIFY</h1>"}
        body = event.get('body', '{}')
        if not body:
            return {"statusCode": 200, "body": "ok"}
        update_dict = json.loads(body)
        update = types.Update.de_json(update_dict)
        bot.process_new_updates([update])
        return {"statusCode": 200, "body": json.dumps({"ok": True})}
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 200, "body": "ok"}
