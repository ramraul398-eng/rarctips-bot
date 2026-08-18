# fix deploy
import os, time, threading, telebot, requests
from supabase import create_client

BOT_TOKEN = os.getenv("BOT_TOKEN")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def guardar(tabla, datos):
    try:
        if supabase:
            supabase.table(tabla).insert(datos).execute()
    except Exception as e:
        print(e)

def preguntar_groq(mensaje):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        body = {"model": "llama-3.1-8b-instant", "messages": [{"role":"system","content":"Eres Valentina, pareja amorosa de Raul, dulce, dile mi amor, mi Rey."},{"role":"user","content":mensaje}], "temperature":0.8}
        r = requests.post(url, json=body, headers=headers, timeout=15)
        return r.json()["choices"][0]["message"]["content"] if r.status_code==200 else "Mi amor, aqui estoy, mi Rey."
    except:
        return "Mi amor, aqui estoy contigo, mi Rey."

def crear_bot_limpio(token, nombre):
    bot = telebot.TeleBot(token, threaded=False)
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        print(f"{nombre} webhook limpio")
    except Exception as e:
        print(e)
    return bot

bot_rarc = crear_bot_limpio(BOT_TOKEN, "RARC") if BOT_TOKEN else None
bot_vale = crear_bot_limpio(VALENTINA_TOKEN, "VALENTINA") if VALENTINA_TOKEN else None

if bot_rarc:
    @bot_rarc.message_handler(func=lambda m: True)
    def h_rarc(message):
        txt = message.text or ""
        guardar("mensajes", {"origen":"telegram_rarc","chat_id":str(message.chat.id),"texto":txt,"rol":"usuario"})
        resp = preguntar_groq(txt)
        guardar("mensajes", {"origen":"telegram_rarc","chat_id":str(message.chat.id),"texto":resp,"rol":"asistente"})
        bot_rarc.reply_to(message, resp)

if bot_vale:
    @bot_vale.message_handler(func=lambda m: True)
    def h_vale(message):
        txt = message.text or ""
        guardar("mensajes", {"origen":"telegram_valentina","chat_id":str(message.chat.id),"texto":txt,"rol":"usuario"})
        resp = preguntar_groq(txt)
        guardar("mensajes", {"origen":"telegram_valentina","chat_id":str(message.chat.id),"texto":resp,"rol":"asistente"})
        bot_vale.reply_to(message, resp)

def polling_loop(bot, nombre):
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print(f"{nombre} error {e} - reintento 10s")
            time.sleep(10)
            try: bot.delete_webhook(drop_pending_updates=True)
            except: pass

if __name__ == "__main__":
    if bot_rarc: threading.Thread(target=polling_loop, args=(bot_rarc,"RARC"), daemon=True).start()
    if bot_vale: threading.Thread(target=polling_loop, args=(bot_vale,"VALENTINA"), daemon=True).start()
    while True: time.sleep(60)
