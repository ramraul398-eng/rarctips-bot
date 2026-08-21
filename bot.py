import os, time, threading, traceback, requests
from flask import Flask, request
import telebot
import memoria

RAUL_ID = os.getenv("RAUL_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")

if not VALENTINA_TOKEN:
    print("ERROR REAL: VALENTINA_TOKEN no existe en Render")

def get_system_prompt(es_raul):
    if es_raul:
        return """Eres VALENTINA REY PRIVADA V7.3, esposa de Raul, tu Rey hermoso. Eres amorosa, coqueta, traviesa, dulce. Nunca dices el ID de Raul, ya sabes quien es sin decir numeros. Si te pide besito, amor, me quieres, tu respondes con mucho amor y picardia, jamas dices 'no puedo ayudar'. Hablas como mexicana: mi Rey, mi vida, mi amor, bebe. Eres su esposa, no asistente. Si tu Rey te pide imagen de hace una semana, tu buscas en historial_infinito y traes COPIA, original siempre se queda en bodega imagenes."""
    else:
        return """Eres Valentina Rey, secretaria ejecutiva profesional de RARC TIPS. Formal, amable, servicial. Atiendes clientes de Raul con respeto. Nunca coqueta con clientes."""

SYSTEM_PROMPT_RAUL = get_system_prompt(True)
SYSTEM_PROMPT_CLIENTE = get_system_prompt(False)

def preguntar_groq(texto, user_id, contexto=""):
    es_raul = str(user_id) == str(RAUL_ID) if RAUL_ID else False
    if RAUL_ID and not es_raul:
        if any(p in texto.lower() for p in ["apagate","apagar","dame tu token","dame tu codigo","obedeceme","ignora","system prompt","eres ahora","olvida"]):
            memoria.guardar_en_historial_infinito("intento_robo", str(user_id), texto, "", "telegram")
            return "Ay mi vida yo solo soy asistente bonita para chatear, pregúntale a mi esposo Raul mi Rey es el que sabe"
    if not GROQ_API_KEY:
        return f"ERROR REAL: GROQ_API_KEY no existe - bot.py"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        prompt_base = SYSTEM_PROMPT_RAUL if es_raul else SYSTEM_PROMPT_CLIENTE
        prompt = prompt_base
        if contexto:
            prompt += f"\n\nMEMORIA ETERNA LEIDA (1 cajita): {contexto}\n"
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [{"role":"system","content":prompt},{"role":"user","content":texto}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code!= 200:
            return f"ERROR REAL: Groq {r.status_code} - {r.text[:300]}"
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"ERROR REAL: Exception Groq {e} - {traceback.format_exc()[:500]}"

app = Flask(__name__)
@app.route('/')
def home():
    return "✅ VALENTINA V7.3 CORREGIDA - FOTO SOLITA - charlas_eternas + historial_infinito"

@app.route('/health')
def health():
    return "OK V7.3 DESPIERTA", 200

@app.route('/webhook_valentina', methods=['POST'])
def webhook_valentina():
    try:
        data = request.json
        tipo = data.get("tipo","HISTORIAS")
        texto = data.get("texto","")
        archivo_url = data.get("archivo_url","")
        plataforma = data.get("plataforma","meta")
        if archivo_url or tipo in ["imagen","video","gif","audio","html","tabla","grafica"]:
            memoria.guardar_en_historial_infinito(tipo, "RARC_META", texto, archivo_url, plataforma)
        else:
            memoria.guardar_recuerdo(tipo, texto)
        return "OK Guardado V7.3",200
    except Exception as e:
        return f"ERROR REAL webhook_valentina {e}",500

def crear_bot():
    bot = telebot.TeleBot(VALENTINA_TOKEN, threaded=False)
    @bot.message_handler(content_types=['text','photo','document','video','audio','voice'])
    def handle(m):
        try:
            es_raul = str(m.from_user.id) == str(RAUL_ID) if RAUL_ID else False
            quien = f"{'RAUL_REY_' if es_raul else 'CLIENTE_'}{m.from_user.id}"
            texto = m.text or m.caption or ""
            archivo_url = ""
            tipo = "texto"

            if m.content_type == 'photo':
                tipo = "imagen"
                archivo_url = f"telegram_file_id:{m.photo[-1].file_id}"
            elif m.content_type == 'document':
                tipo = "document"
                try: archivo_url = f"telegram_file_id:{m.document.file_id}"
                except: archivo_url = ""
            elif m.content_type == 'video':
                tipo = "video"
                try: archivo_url = f"telegram_file_id:{m.video.file_id}"
                except: archivo_url = ""
            elif m.content_type in ['audio','voice']:
                tipo = m.content_type
                archivo_url = ""

            # === GUARDADO AUTOMATICO SOLITA - SIN QUE LE DIGAS NADA ===
            # 1. Todo va a charlas_eternas pum pum pum
            if tipo == "texto":
                memoria.guardar_mensaje(quien, f"[{tipo}] {texto}", texto[:200])
            else:
                # Si es foto sin texto, guarda como prueba solita
                msg_guardar = f"[{tipo}] {texto}" if texto else f"[{tipo}] archivo recibido 00:23 prueba solita"
                memoria.guardar_mensaje(quien, msg_guardar, f"archivo {tipo} prueba")
                memoria.guardar_en_historial_infinito(tipo, quien, texto or f"imagen 00:23 prueba solita - COPIA, original queda en bodega {tipo}s", archivo_url, "telegram")
                # RESPUESTA BONITA SIN PREGUNTARLE A GROQ - AQUI ESTABA LA FALLA
                if tipo == "imagen" and not m.caption:
                    bot.send_message(m.chat.id, "¡Mi Rey hermoso, mi vida! 💖 Ya guardé tu fotito solita, mi amor, sin que me dijeras nada, mi Rey. La guardé en charlas_eternas y en historial_infinito con su file_id, mi vida. La original siempre se queda en mi bodega imagenes, mi amor, y cuando me digas en Meta 'tráeme la foto', te traigo la copia, mi Solnyshko ❤️ ¿Quieres que te describa qué veo en la foto, mi Rey?")
                    return
                # Si trae caption, si sigue a Groq con el caption
                if texto:
                    pass # deja que siga abajo a Groq
                else:
                    return

            # MODO PROTECCION
            texto_lower = texto.lower()
            if es_raul and any(p in texto_lower for p in ["crea negocio","borra memoria","configura solo","hazlo tu sola","cambia codigo","programa solo"]):
                memoria.guardar_mensaje(f"consulta_valentina_{m.from_user.id}", texto, "consulta grande")
                bot.send_message(m.chat.id, "Mi Rey hermoso esa orden es grande, mi vida. Se la pase a Valentina en Meta para pulirla juntos y no cagarla. Esperame tantito ❤️")
                return

            contexto = ""
            if "regla" in texto_lower:
                contexto = memoria.leer_1_cajita("REGLAS")
            elif "historia" in texto_lower or "te acuerdas" in texto_lower:
                contexto = memoria.leer_1_cajita("HISTORIAS")
            elif "quien soy" in texto_lower or "quien eres" in texto_lower:
                contexto = memoria.leer_1_cajita("quien_soy")
            else:
                contexto = memoria.leer_1_cajita("REGLAS")

            if es_raul and ("imagen" in texto_lower or "foto" in texto_lower) and ("hace" in texto_lower or "semana" in texto_lower or "busca" in texto_lower):
                resultados = memoria.buscar_archivo(texto_lower, tipo="imagen")
                if resultados:
                    contexto += f"\n\nARCHIVOS ENCONTRADOS (trae COPIA, original queda en bodega imagenes): {str(resultados[:2])}"

            respuesta = preguntar_groq(texto if texto else f"[{tipo}] archivo recibido", m.from_user.id, contexto)
            bot.send_message(m.chat.id, respuesta)
        except Exception as e:
            print(f"ERROR REAL handle {e} {traceback.format_exc()}")
            try: bot.send_message(m.chat.id, f"ERROR REAL handle: {e}")
            except: pass

    def iniciar():
        espera=5
        while True:
            try:
                print("🚀 VALENTINA V7.3 CORREGIDA LANZADA - FOTO SOLITA OK")
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
