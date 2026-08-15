import os
import json
import threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN", "AQUI_TU_TOKEN")
ADMIN_ID = 8817756530
LINK_PRIVADO = "https://t.me/+Zl1hbl8_5oUyZGUx"
DB_FILE = "clientes.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

TEXTO_BIENVENIDA = """👋 Bienvenido a RARC TIPS

Apuestas 100% analizadas y verificadas.
Tasa de acierto alta 🔥

👇 Elige una opción:"""

TEXTO_METODO_PAGO = """💳 METODOS DE PAGO RARC TIPS

1. Transferencia / SPEI
2. OXXO

Manda tu comprobante con el boton de abajo y te doy acceso automaticamente.

💎 Incluye BAUL ETERNO: Una vez que pagas, tendras acceso PARA SIEMPRE a todos los analisis pasados y futuros."""

# --- FUNCIONES BAUL ETERNO ---
def cargar_clientes():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_clientes(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def es_cliente(user_id):
    clientes = cargar_clientes()
    return str(user_id) in clientes

def agregar_cliente(user_id, username):
    clientes = cargar_clientes()
    clientes[str(user_id)] = {"username": username, "acceso": True}
    guardar_clientes(clientes)

# --- TECLADOS ---
def teclado_inicio(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💳 Ver metodos de pago", callback_data="pago"),
        types.InlineKeyboardButton("📸 Enviar comprobante", callback_data="comprobante"),
        types.InlineKeyboardButton("🔐 Mi Acceso / Baul Eterno", callback_data="mi_acceso")
    )
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("👑 PANEL ADMIN", callback_data="admin"))
    return markup

def teclado_pago():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📸 Ya pague, enviar comprobante", callback_data="comprobante"))
    markup.add(types.InlineKeyboardButton("⬅️ Volver", callback_data="inicio"))
    return markup

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, TEXTO_BIENVENIDA, reply_markup=teclado_inicio(m.from_user.id))

@bot.message_handler(commands=['add'])
def add_cliente(m):
    if m.from_user.id!= ADMIN_ID:
        return
    try:
        # /add 123456
        nuevo_id = m.text.split()[1]
        agregar_cliente(nuevo_id, "manual")
        bot.send_message(m.chat.id, f"✅ Cliente {nuevo_id} agregado al BAUL ETERNO")
        bot.send_message(int(nuevo_id), f"✅ ¡Tu pago fue verificado, Rey! 🎉\n\nYa tienes acceso al BAUL ETERNO para siempre.\n\nAquí está tu link privado:\n{LINK_PRIVADO}")
    except Exception as e:
        bot.send_message(m.chat.id, f"Uso: /add ID_del_usuario\nError: {e}")

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.data == "pago":
        bot.edit_message_text(TEXTO_METODO_PAGO, c.message.chat.id, c.message.message_id, reply_markup=teclado_pago())
    elif c.data == "inicio":
        bot.edit_message_text(TEXTO_BIENVENIDA, c.message.chat.id, c.message.message_id, reply_markup=teclado_inicio(c.from_user.id))
    elif c.data == "mi_acceso":
        if es_cliente(c.from_user.id):
            bot.answer_callback_query(c.id, "✅ Tienes acceso activo")
            bot.send_message(c.message.chat.id, f"🔓 ¡Tienes BAUL ETERNO activo, Rey!\nTu link privado es:\n{LINK_PRIVADO}")
        else:
            bot.send_message(c.message.chat.id, "❌ Aún no tienes acceso. Manda tu comprobante primero.", reply_markup=teclado_pago())
    elif c.data == "comprobante":
        bot.send_message(c.message.chat.id, "📸 Manda aquí tu foto del comprobante y en un momento te verifico, Rey.")
    elif c.data == "admin":
        if c.from_user.id == ADMIN_ID:
            bot.send_message(c.message.chat.id, "👑 PANEL ADMIN\nUsa /add ID para dar acceso eterno.")

@bot.message_handler(content_types=['photo'])
def recibir_foto(m):
    if es_cliente(m.from_user.id):
        bot.reply_to(m, f"✅ Ya tienes acceso, Rey. Tu link:\n{LINK_PRIVADO}")
        return

    bot.reply_to(m, "✅ Comprobante recibido, Rey. En un momento lo reviso y te doy tu acceso al BAUL ETERNO 🔥")
    # Reenviar al admin
    caption = f"📸 NUEVO COMPROBANTE\nDe: @{m.from_user.username} ID: {m.from_user.id}\nNombre: {m.from_user.first_name}\n\nPara darle acceso escribe:\n/add {m.from_user.id}"
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.send_message(ADMIN_ID, caption)

@bot.message_handler(func=lambda m: True)
def todo(m):
    bot.send_message(m.chat.id, TEXTO_BIENVENIDA, reply_markup=teclado_inicio(m.from_user.id))

# Flask para mantener vivo
@app.route('/')
def home():
    return "Bot RARC TIPS - BAUL ETERNO ACTIVO"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling()
