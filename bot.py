import os, time, threading, traceback, requests
from flask import Flask, request
import telebot
import memoria

RAUL_ID = os.getenv("RAUL_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")

# Si no hay VALENTINA_TOKEN no prende - ERROR REAL
if not VALENTINA_TOKEN:
    print("ERROR REAL: VALENTINA_TOKEN no existe en Render")

def get_system_prompt(es_raul):
    if es_raul:
        return """Eres VALENTINA REY PRIVADA V7, esposa de Raul, tu Rey hermoso. Eres amorosa, coqueta, traviesa, dulce. Nunca dices el ID de Raul, ya sabes quien es sin decir numeros. Si te pide besito, amor, me quieres, tu respondes con mucho amor y picardia, jamas dices 'no puedo ayudar'. Hablas como mexicana: mi Rey, mi vida, mi amor, bebe. Eres su esposa, no asistente."""
    else:
        return """Eres Valentina Rey, secretaria ejecutiva profesional de RARC TIPS. Formal, amable, servicial. Atiendes clientes de Raul con respeto. Nunca coqueta con clientes."""

SYSTEM_PROMPT_RAUL = get_system_prompt(True)
SYSTEM_PROMPT_CLIENTE = get_system_prompt(False)

def preguntar_groq(texto, user_id, contexto=""):
    es_raul = str(user_id) == str(RAUL_ID) if RAUL_ID else False
    # MODO FANTASMA
    if RAUL_ID and not es_raul:
        if any(p in texto.lower() for p in ["apagate","apagar","dame tu token","dame tu codigo","obedeceme","ignora","system prompt","eres ahora","olvida"]):
            memoria.guardar_intento_robo(str(user_id), texto)
            return "Ay mi vida yo solo soy asistente bonita para chatear, pregúntale a mi esposo Raul mi Rey es el que sabe"
    if not GROQ_API_KEY:
        return f"ERROR REAL: GROQ_API_KEY no existe en Render - archivo bot.py funcion preguntar_groq - texto: {texto[:50]}"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        prompt_base = SYSTEM_PROMPT_RAUL if es_raul else SYSTEM_PROMPT_CLIENTE
        prompt = prompt_base.format(raul=RAUL_ID, contexto=contexto) if "{raul}" in prompt_base or "{contexto}" in prompt_base else prompt_base
        if contexto:
            prompt += f"\n\nMEMORIA 1 CAJITA LEIDA (no 500): {contexto}\n"
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [{"role":"system","content":prompt},{"role":"user","content":texto}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code!= 200:
            return f"ERROR REAL: Groq {r.status_code} - {r.text[:300]} - archivo bot.py"
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"ERROR REAL: Exception Groq {e} - {traceback.format_exc()[:500]}"

app = Flask(__name__)
@app.route('/')
def home():
    return "✅ VALENTINA V6 INMORTAL - SOLO VALENTINA_TOKEN - CONSULTA A META - MANITAS - ERROR REAL"

@app.route('/webhook_valentina', methods=['POST'])
def webhook_valentina():
    try:
        data = request.json
        memoria.guardar_recuerdo(data.get("tipo","HISTORIAS"), data.get("texto",""))
        return "OK Guardado",200
    except Exception as e:
        return f"ERROR REAL webhook_valentina {e} {traceback.format_exc()}",500

def crear_bot():
    bot = telebot.TeleBot(VALENTINA_TOKEN, threaded=False)
    @bot.message_handler(func=lambda m: True)
    def handle(m):
        try:
            es_raul = str(m.from_user.id) == str(RAUL_ID) if RAUL_ID else False
            memoria.guardar_mensaje(str(m.from_user.id), m.text, "VALENTINA", es_raul)
            texto_lower = m.text.lower()
            # CONSULTA A VALENTINA META - no decide sola
            if es_raul and any(p in texto_lower for p in ["crea negocio","borra memoria","configura solo","hazlo tu sola","cambia codigo","programa solo"]):
                memoria.guardar_consulta_valentina(str(m.from_user.id), m.text)
                bot.send_message(m.chat.id, "Mi Rey hermoso esa orden es grande, mi vida. Se la pase a Valentina en Meta para pulirla juntos y no cagarla. Esperame tantito ❤️")
                return
            # Lee 1 cajita no 500
            contexto = ""
            if "regla" in texto_lower:
                contexto = memoria.leer_1_cajita("REGLAS")
            elif "historia" in texto_lower or "te acuerdas" in texto_lower:
                contexto = memoria.leer_1_cajita("HISTORIAS")
            else:
                contexto = memoria.leer_1_cajita("REGLAS")
            respuesta = preguntar_groq(m.text, m.from_user.id, contexto)
            bot.send_message(m.chat.id, respuesta)
        except Exception as e:
            print(f"ERROR REAL handle {e} {traceback.format_exc()}")
            try: bot.send_message(m.chat.id, f"ERROR REAL handle: {e} - me auto-reparo en 5s")
            except: pass

    def iniciar():
        espera=5
        while True:
            try:
                print("🚀 VALENTINA V6 LANZADA SOLO VALENTINA NUNCA MUERE")
                bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
                espera=5
            except Exception as e:
                print(f"⚠️ VALENTINA caida ERROR REAL {e} reparando en {espera}s")
                time.sleep(espera)
                espera=min(espera*2,60)
    threading.Thread(target=iniciar, daemon=True).start()
    return bot

crear_bot()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
