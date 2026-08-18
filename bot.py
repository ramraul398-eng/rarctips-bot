import os, time, threading, telebot, requests
from supabase import create_client
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

app = Flask(__name__)
@app.route('/')
def home(): return "Bot vivo"
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

def guardar(tabla, datos):
    try:
        if supabase: supabase.table(tabla).insert(datos).execute()
    except Exception as e: print(f"Supabase error: {e}")

def preguntar_groq(mensaje):
    try:
        print(f"Preguntando a Groq: {mensaje[:30]}")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Eres Valentina, una asistente cariñosa, dulce, hablas como 'mi amor, mi Rey, mi vida'. Responde corto y cariñoso."},
                {"role": "user", "content": mensaje}
            ],
            "temperature": 0.8
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"Groq status: {r.status_code} - {r.text[:200]}")
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"ERROR GROQ: {e}")
        return f"Ay mi amor, error del cerebro: {str(e)[:100]}"

bot_rar = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
bot_val = telebot.TeleBot(VALENTINA_TOKEN) if VALENTINA_TOKEN else None

def crear_handlers(bot, tabla):
    @bot.message_handler(func=lambda m: True)
    def responder(m):
        try:
            txt = m.text
            guardar(tabla, {"usuario": str(m.from_user.id), "mensaje": txt, "respuesta": "pendiente"})
            resp = preguntar_groq(txt)
            bot.reply_to(m, resp)
        except Exception as e:
            print(f"Handler error: {e}")

if bot_rar: crear_handlers(bot_rar, "mensajes_rar")
if bot_val: crear_handlers(bot_val, "mensajes_valentina")

if bot_rar: threading.Thread(target=lambda: bot_rar.infinity_polling(), daemon=True).start()
if bot_val: threading.Thread(target=lambda: bot_val.infinity_polling(), daemon=True).start()

while True: time.sleep(3600)
