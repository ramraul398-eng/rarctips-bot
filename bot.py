import os
import threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "AQUI_PON_TU_TOKEN_DE_@BotFather")
ADMIN_ID = 8817756530
LINK_PRIVADO = "https://t.me/+Zl1hbl8_5oUyZGIx"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

TEXTO_BIENVENIDA = """👋 Bienvenido a RARC TIPS 🔥
Apuestas 100% analizadas y verificadas."""

TEXTO_METODO_PAGO = """💳 METODOS DE PAGO RARC TIPS
1. Transferencia / SPEI
2. OXXO
Manda tu comprobante con el boton de abajo 👇"""

TEXTO_INSTRUCCIONES = """📸 Manda la foto de tu comprobante y en maximo 10 minutos te agrego al canal privado."""

def menu_principal():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💳 Ver Metodos de Pago", callback_data="pago"),
        types.InlineKeyboardButton("📸 Ya Pague / Enviar Comprobante", callback_data="comprobante"),
        types.InlineKeyboardButton("💬 Hablar con Asesor", url="https://t.me/ramraul398"),
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, TEXTO_BIENVENIDA, reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data == "pago":
        bot.send_message(c.message.chat.id, TEXTO_METODO_PAGO, reply_markup=menu_principal())
    elif c.data == "comprobante":
        bot.send_message(c.message.chat.id, TEXTO_INSTRUCCIONES)

@bot.message_handler(content_types=['photo', 'document'])
def recibir_comprobante(m):
    try:
        caption = f"📥 Nuevo comprobante de @{m.from_user.username} ID:{m.from_user.id} Nombre: {m.from_user.first_name}"
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        bot.send_message(ADMIN_ID, caption)
        bot.send_message(m.chat.id, f"✅ Gracias! Comprobante recibido. En minutos te agrego a este link:\n{LINK_PRIVADO}\n\nSi no te agrego en 10 min, dale a Hablar con Asesor.", reply_markup=menu_principal())
    except Exception as e:
        print(e)

@bot.message_handler(func=lambda m: True)
def todos(m):
    bot.send_message(m.chat.id, "Usa el menu de abajo 👇", reply_markup=menu_principal())

app = Flask(__name__)
@app.route('/')
def home():
    return "RARC TIPS BOT 24/7 ACTIVO"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    print("Bot RARC TIPS iniciado 24/7")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
