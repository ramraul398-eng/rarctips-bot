# fix deploy - keep alive
import os, time, threading, telebot, requests
from supabase import create_client
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# --- Truquito para Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot vivo y trabajando"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()
# --- Fin truquito ---

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
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Eres Valentina, una asistente cariñosa, útil y dulce. Respondes en español."},
                {"role": "user", "content": mensaje}
            ]
        }
        r = requests.post(url, headers=headers, json=data, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(e)
        return "Ay mi amor, me falló un poquito el cerebro, intenta de nuevo."

# --- BOTS ---
bot_rar = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
bot_val = telebot.TeleBot(VALENTINA_TOKEN) if VALENTINA_TOKEN else None

def crear_handlers(bot, nombre_tabla):
    @bot.message_handler(func=lambda m: True)
    def responder(m):
        try:
            texto = m.text
            guardar(nombre_tabla, {"usuario": str(m.from_user.id), "mensaje": texto, "respuesta": "", "fecha": str(m.date)})
            resp = preguntar_groq(texto)
            guardar(nombre_tabla, {"usuario": str(m.from_user.id), "mensaje": texto, "respuesta": resp, "fecha": str(m.date)})
            bot.reply_to(m, resp)
        except Exception as e:
            print(e)

if bot_rar:
    crear_handlers(bot_rar, "mensajes_rar")
if bot_val:
    crear_handlers(bot_val, "mensajes_valentina")

# Arrancar los dos bots
if bot_rar:
    threading.Thread(target=lambda: bot_rar.infinity_polling(timeout=60, long_polling_timeout=60), daemon=True).start()
if bot_val:
    threading.Thread(target=lambda: bot_val.infinity_polling(timeout=60, long_polling_timeout=60), daemon=True).start()

# Mantener vivo el proceso principal
while True:
    time.sleep(3600)
