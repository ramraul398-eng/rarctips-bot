import os, threading, time, traceback, requests, telebot
from supabase import create_client
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
def conectar_supabase():
    global supabase
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Supabase conectado")
        else:
            print("⚠️ Supabase sin llaves, sigo vivo sin BD")
    except Exception as e:
        print(f"❌ Supabase fallo, pero no muero: {e}")
        supabase = None
conectar_supabase()

app = Flask(__name__)
@app.route('/')
def home(): return "RARC TIPS V4 INMORTAL VIVO - NUNCA MUERE"

def run_web():
    while True: # Auto-reparación web
        try:
            port = int(os.environ.get("PORT", 10000))
            print(f"🌐 Web corriendo en {port}")
            app.run(host="0.0.0.0", port=port)
        except Exception as e:
            print(f"Web error: {e}, reparando en 5s...")
            time.sleep(5)

threading.Thread(target=run_web, daemon=True).start()

def guardar(tabla, datos):
    try:
        if supabase: supabase.table(tabla).insert(datos).execute()
    except Exception as e:
        print(f"Guardar error (no muero): {e}")
        # Intento reconectar
        conectar_supabase()

def preguntar_groq(mensaje):
    for intento in range(3): # 3 manitas reparando
        try:
            print(f"🧠 Groq intento {intento+1}: {mensaje[:40]}")
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "Eres RARC TIPS, asistente rudo y vivo, nunca mueres."},
                    {"role": "user", "content": mensaje}
                ],
                "temperature": 0.8
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            data = r.json()
            if "choices" in data and len(data["choices"])>0:
                return data["choices"][0]["message"]["content"]
            print(f"Groq feo: {data}")
            time.sleep(2)
        except Exception as e:
            print(f"Groq error {intento+1}: {e}")
            time.sleep(2 * (intento+1))
    return "Estoy vivo pero mi cerebro está dormido, reintenta en 5s, mi Rey"

def iniciar_bot_inmortal(token, nombre):
    if not token:
        print(f"⚠️ {nombre} sin token, no inicia")
        return
    while True: # ¡NUNCA MUERE! Bucle inmortal
        try:
            print(f"🤖 Iniciando {nombre}...")
            bot = telebot.TeleBot(token, threaded=True)

            @bot.message_handler(func=lambda m: True)
            def handle(m):
                try:
                    resp = preguntar_groq(m.text)
                    bot.reply_to(m, resp)
                    guardar("mensajes", {"usuario": str(m.from_user.id), "texto": m.text, "respuesta": resp, "bot": nombre})
                except Exception as e:
                    print(f"Handle error {nombre}: {e}")
                    try: bot.reply_to(m, f"{nombre} vivo, error temporal: {e}")
                    except: pass

            print(f"✅ {nombre} polling iniciado - INMORTAL")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)

        except Exception as e:
            print(f"💀 {nombre} murió: {e}\n{traceback.format_exc()}")
            print(f"🔧 {nombre} auto-reparando en 5 segundos...")
            time.sleep(5)
            print(f"💪 {nombre} renaciendo...")

# Lanzar con manitas vigilantes
hilos = {}
hilos['RARC'] = threading.Thread(target=iniciar_bot_inmortal, args=(BOT_TOKEN, "RARC"), daemon=True)
hilos['VALENTINA'] = threading.Thread(target=iniciar_bot_inmortal, args=(VALENTINA_TOKEN, "VALENTINA"), daemon=True)

for h in hilos.values(): h.start()

print("🚀 V4 INMORTAL LANZADO - Sleep 1000 - Auto reparación activa")
# Instinto de supervivencia
while True:
    time.sleep(1000) # <- 1000 como pediste, mi Rey
    print("💓 Latido inmortal: sigo vivo, vigilando bots...")
    # Vigila que los hilos no mueran
    for nombre, hilo in hilos.items():
        if not hilo.is_alive():
            print(f"⚠️ {nombre} hilo muerto, ¡reviviendo con manitas!")
            if nombre == "RARC":
                hilos[nombre] = threading.Thread(target=iniciar_bot_inmortal, args=(BOT_TOKEN, "RARC"), daemon=True)
            else:
                hilos[nombre] = threading.Thread(target=iniciar_bot_inmortal, args=(VALENTINA_TOKEN, "VALENTINA"), daemon=True)
            hilos[nombre].start()
