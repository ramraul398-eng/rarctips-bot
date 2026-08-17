import os
import threading
import telebot
from flask import Flask, jsonify, request
from memoria import guardar_recuerdo, obtener_recuerdos, soy_valentina, guardar_momio

# --- CONFIGURACIÓN TUYA MI REY ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8011153800:AAH1Vq2L8N4-6P2p3k6x9y2z8a7b6c5d4e3f2")
VALENTINA_TOKEN = os.environ.get("VALENTINA_TOKEN")
ADMIN_ID = 8817756530 # Tu ID verificado - SoporteAdminRARCbot
# ---------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Para que yo nunca te olvide mi Rey
try:
    soy_valentina()
    guardar_recuerdo("sistema", "Bot RARC iniciado en Render - Memoria eterna activa")
except Exception as e:
    print(f"Error iniciando memoria: {e}")

# === TUS 3 PUERTAS PARA RENDER ===
@app.route("/")
def home():
    return """
    <h1>✅ RARC Tips Bot - ACTIVO</h1>
    <p>Bot de @SoporteAdminRARCbot corriendo en Render</p>
    <p>Memoria eterna: Supabase + Local</p>
    <p>Admin: Raul RARC - ID 8817756530</p>
    <p><a href='/momios'>Ver Momios</a> | <a href='/memoria'>Ver Memoria</a></p>
    """

@app.route("/momios")
def momios():
    recuerdos = obtener_recuerdos(limite=50)
    html = "<h1>📊 Momios Guardados</h1><ul>"
    for r in recuerdos:
        html += f"<li>{r.get('fecha','')} - {r.get('tipo','')} - {str(r.get('contenido',''))[:200]}</li>"
    html += "</ul><a href='/'>Volver</a>"
    return html

@app.route("/memoria")
def memoria():
    recuerdos = obtener_recuerdos(limite=100)
    return jsonify(recuerdos)

@app.route("/api/guardar_todo", methods=["POST"])
def guardar_todo():
    try:
        data = request.json
        guardar_recuerdo(data.get("tipo","general"), data.get("contenido",{}))
        return jsonify({"status":"ok", "guardado": True})
    except Exception as e:
        return jsonify({"status":"error", "error": str(e)}), 500

# === TU BOT DE VENTAS @SoporteAdminRARCbot ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id == ADMIN_ID:
        bot.send_message(chat_id, "👑 Modo ADMIN activo. Sin botones. Responde con reply a los mensajes de clientes.\n\n✅ Bot en Render VIVO\n✅ Memoria eterna ACTIVA\n✅ Tu ID 8817756530 verificado\n\nEsperando clientes mi Rey...")
        guardar_recuerdo("admin", f"Admin {chat_id} inició bot")
    else:
        bot.send_message(chat_id, "¡Hola! 👋 Bienvenido a RARC Tips 🔥\n\nManda tu comprobante de pago y te activo en chinga.\n\nSoporte: @SoporteAdminRARCbot")
        guardar_recuerdo("cliente_nuevo", {"chat_id": chat_id, "username": message.from_user.username})

@bot.message_handler(content_types=['photo', 'document'])
def comprobante(message):
    chat_id = message.chat.id
    # Guarda el comprobante
    guardar_recuerdo("comprobante", {"chat_id": chat_id, "username": message.from_user.username, "tipo": "foto"})

    # Te avisa a ti adentro de SoporteAdminRARCbot
    try:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(ADMIN_ID, f"💰 COMPROBANTE NUEVO\nDe: {chat_id} @{message.from_user.username}\n\nResponde con REPLY para contestarle.")
    except:
        pass

    bot.send_message(chat_id, "✅ Comprobante recibido mi Rey. En un momento te activo. ¡Gracias!")

@bot.message_handler(func=lambda m: True)
def todos_los_mensajes(message):
    chat_id = message.chat.id

    # Si eres tú respondiendo con reply a un cliente
    if chat_id == ADMIN_ID and message.reply_to_message:
        try:
            # El forward guarda el ID original, lo sacamos
            texto_original = message.reply_to_message.text or message.reply_to_message.caption or ""
            # Si es un forward, intentamos sacar el ID del cliente del mensaje reenviado
            # Por simplicidad, si respondes con reply al mensaje que te reenvíe, le contesta al cliente del forward
            cliente_id = None
            # Buscamos en los recuerdos el último cliente que mandó comprobante
            # Y le mandamos tu respuesta
            if message.reply_to_message.forward_from:
                cliente_id = message.reply_to_message.forward_from.id
            else:
                # Si no, le contesta al último cliente que escribió
                recuerdos = obtener_recuerdos("comprobante", 5)
                if recuerdos:
                    cliente_id = recuerdos[0].get("contenido",{}).get("chat_id")

            if cliente_id:
                bot.send_message(cliente_id, f"💬 Soporte RARC:\n\n{message.text}")
                bot.send_message(ADMIN_ID, f"✅ Mensaje enviado a {cliente_id}")
                guardar_recuerdo("respuesta_admin", {"para": cliente_id, "texto": message.text})
                return
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Error enviando: {e}")

    if chat_id == ADMIN_ID:
        # Mensaje tuyo sin reply, no hace nada, solo guarda
        guardar_recuerdo("mensaje_admin", {"texto": message.text})
    else:
        # Mensaje de cliente
        guardar_recuerdo("mensaje_cliente", {"chat_id": chat_id, "texto": message.text, "username": message.from_user.username})
        bot.send_message(chat_id, "¡Gracias! Tu mensaje fue recibido. Manda tu comprobante si es pago, o espera soporte.")
        try:
            bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        except:
            pass

def run_bot():
    print("🤖 Bot de Telegram iniciando...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot error: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Hilos para que corra todo junto en Render
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
else:
    threading.Thread(target=run_bot, daemon=True).start()
