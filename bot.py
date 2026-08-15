import os
import re
import threading
import requests
import json
import time
from flask import Flask, request, jsonify
import telebot
from telebot import types
from datetime import datetime
from pathlib import Path
import base64
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8817756530
LINK_PRIVADO = "https://t.me/+Zl1hbl8_5oUyZGIx"
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "2c3c27028fd3d485491d497cbd5bab72de")
ZONA_GDL = ZoneInfo("America/Mexico_City")
DB_FILE = "clientes.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML") if BOT_TOKEN else None
ULTIMO_CLIENTE = None
app = Flask(__name__)

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
    return str(user_id) in cargar_clientes()

def agregar_cliente(user_id, username):
    clientes = cargar_clientes()
    clientes[str(user_id)] = {"username": username, "acceso": True, "fecha": str(datetime.now(ZONA_GDL))}
    guardar_clientes(clientes)

TEXTO_INFO = """Hola
Qué gusto tu interés en unirte a RARC TIPS
Aquí nos enfocamos en analizar a fondo los mejores eventos del día para darte los tips deportivos con mayor probabilidad de resultado.
Nuestro objetivo es que vayas a la segura y maximices tus ganancias.

¿Qué incluye tu acceso al canal blindado?
Tips diarios, Cuotas con valor, Alertas en vivo.
Costo: Solo $350 pesos mensuales.
Dime y te paso la cuenta para darte de alta.

Tu eliges tu casa de apuestas
💎 Incluye BAUL ETERNO: Acceso para siempre."""

TEXTO_PAGO = """Hola
El acceso a nuestro canal privado y blindado incluye todo nuestro contenido exclusivo por solo $350 pesos mensuales.

💳 Transferencia Bancaria (México):
Banco: BBVA
CLABE / Cuenta: 012 320 01543721884 3
Nombre: Raul Ramirez

Si prefieres OXXO, Mercado Pago o PayPal, avísame.

En cuanto realices tu depósito, dale al botón de enviar comprobante.
¡Te espero dentro!"""

TEXTO_COMP_BOTON = """Para enviar tu comprobante dale al clip que está en la barra de enviar mensaje y adjunta tu recibo. En cuanto el sistema lo detecta te envía el link privado del canal."""

TEXTO_GRACIAS_COMPROBANTE = f"""Muchas gracias por tu confianza y por realizar tu pago para unirte a RARC TIPS.
Aquí tienes tu enlace exclusivo:

{LINK_PRIVADO}

Al presionar el enlace te aparecerá "Solicitar unirse al canal". Presiónalo.
Bienvenido al equipo
🔓 ¡Ya tienes BAUL ETERNO activo para siempre!"""

TEXTO_ASESOR = """Para hablar con un asesor escribe directamente por este chat enseguida serás atendido
@SoporteAdminRARCbot"""

Path("memoria_eterna/chat").mkdir(parents=True, exist_ok=True)
CHAT_FILE = "memoria_eterna/chat/HISTORIAL_INFINITO.txt"
MOMIOS_FILE = "memoria_eterna/momios_tiempo_real.json"
ALERTAS_FILE = "memoria_eterna/alertas_3_niveles.json"
CONTROL_FILE = "memoria_eterna/ultimo_escaneo.json"

if not os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"[{datetime.now(ZONA_GDL)}] SISTEMA: Iniciado\n")
if not os.path.exists(ALERTAS_FILE):
    with open(ALERTAS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"nivel_80_87_gratis": [], "nivel_88_94_oro": [], "nivel_95_100_diamante": []}, f)
if not os.path.exists(CONTROL_FILE):
    with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
        json.dump({"ultima_fecha": "", "ultima_hora_escaneada": -1}, f)

def menu_cliente():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("ℹ️ Solicitar Informacion"), types.KeyboardButton("💳 Metodo de Pago"),
          types.KeyboardButton("📸 Enviar Comprobante"), types.KeyboardButton("💬 Hablar con Asesor"))
    m.add(types.KeyboardButton("🔐 Mi Acceso / Baul Eterno"))
    return m

def menu_admin():
    return types.ReplyKeyboardRemove()

if bot:
    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID and "Solicitar Informacion" in m.text)
    def btn_info(m):
        bot.send_message(m.chat.id, TEXTO_INFO, reply_markup=menu_cliente())

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID and "Metodo de Pago" in m.text)
    def btn_pago(m):
        bot.send_message(m.chat.id, TEXTO_PAGO, reply_markup=menu_cliente())

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID and "Enviar Comprobante" in m.text)
    def btn_comp(m):
        bot.send_message(m.chat.id, TEXTO_COMP_BOTON, reply_markup=menu_cliente())

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID and "Hablar con Asesor" in m.text)
    def btn_asesor(m):
        bot.send_message(m.chat.id, TEXTO_ASESOR, reply_markup=menu_cliente())
        try:
            bot.send_message(ADMIN_ID, f"🆘 Cliente quiere asesor ID:{m.from_user.id}")
        except:
            pass

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID and "Mi Acceso" in m.text)
    def btn_acceso(m):
        if es_cliente(m.from_user.id):
            bot.send_message(m.chat.id, f"🔓 ¡Tienes BAUL ETERNO activo!\nTu link:\n{LINK_PRIVADO}", reply_markup=menu_cliente())
        else:
            bot.send_message(m.chat.id, "❌ Aún no tienes acceso al Baul Eterno. Manda tu comprobante con 📸", reply_markup=menu_cliente())

    @bot.message_handler(commands=['start'])
    def start(m):
        global ULTIMO_CLIENTE
        if m.from_user.id == ADMIN_ID:
            bot.send_message(m.chat.id, "👋 Modo ADMIN activo. Comandos: /add ID", reply_markup=menu_admin())
        else:
            ULTIMO_CLIENTE = m.from_user.id
            bot.send_message(m.chat.id, "👋 Bienvenido a RARC TIPS 🔥", reply_markup=menu_cliente())

    @bot.message_handler(commands=['add'])
    def add_cliente(m):
        if m.from_user.id!= ADMIN_ID:
            return
        try:
            nuevo_id = m.text.split()[1]
            agregar_cliente(nuevo_id, "manual")
            bot.send_message(m.chat.id, f"✅ Cliente {nuevo_id} agregado al BAUL ETERNO", reply_markup=menu_admin())
            try:
                bot.send_message(int(nuevo_id), f"✅ ¡Pago verificado! Ya tienes BAUL ETERNO.\nLink:\n{LINK_PRIVADO}")
            except:
                pass
        except Exception as e:
            bot.send_message(m.chat.id, f"Uso: /add ID\nError: {e}", reply_markup=menu_admin())

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID, content_types=['photo','document','video'])
    def recibir_comprobante(m):
        global ULTIMO_CLIENTE
        ULTIMO_CLIENTE = m.from_user.id
        agregar_cliente(m.from_user.id, m.from_user.username or m.from_user.first_name)
        bot.send_message(m.chat.id, TEXTO_GRACIAS_COMPROBANTE, reply_markup=menu_cliente())
        header = f"📩 Nuevo comprobante de {m.from_user.first_name} ID:{m.from_user.id} - YA AGREGADO AL BAUL"
        try:
            if m.content_type == 'photo':
                bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=f"{header}\n\n{m.caption or ''}")
            elif m.content_type == 'document':
                bot.send_document(ADMIN_ID, m.document.file_id, caption=header)
            else:
                bot.send_video(ADMIN_ID, m.video.file_id, caption=header)
        except:
            pass

    @bot.message_handler(func=lambda m: m.from_user.id!= ADMIN_ID, content_types=['text'])
    def texto_cliente(m):
        global ULTIMO_CLIENTE
        if "Solicitar Informacion" in m.text or "Metodo de Pago" in m.text or "Enviar Comprobante" in m.text or "Hablar con Asesor" in m.text or "Mi Acceso" in m.text or m.text == "/start":
            return
        ULTIMO_CLIENTE = m.from_user.id
        try:
            bot.send_message(ADMIN_ID, f"📩 De {m.from_user.first_name} ID:{m.from_user.id}\n\n{m.text}")
        except:
            pass

    @bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.reply_to_message is not None)
    def admin_reply(m):
        try:
            uid = int(re.search(r"ID:(\d+)", m.reply_to_message.caption or m.reply_to_message.text or "").group(1))
            if m.content_type == 'text':
                bot.send_message(uid, m.text)
            elif m.content_type == 'photo':
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
            else:
                bot.send_message(uid, m.text)
            bot.send_message(ADMIN_ID, f"✅ Enviado a {uid}", reply_markup=menu_admin())
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Error: {e}")

    @bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.reply_to_message is None and m.content_type == 'text' and not m.text.startswith('/'))
    def admin_sin_reply(m):
        global ULTIMO_CLIENTE
        if not ULTIMO_CLIENTE:
            bot.send_message(ADMIN_ID, "⚠️ Responde con reply a un mensaje del cliente.", reply_markup=menu_admin())
            return
        try:
            bot.send_message(ULTIMO_CLIENTE, m.text)
            bot.send_message(ADMIN_ID, f"✅ Enviado a {ULTIMO_CLIENTE}", reply_markup=menu_admin())
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Error: {e}")

def escanear_ahorro(ronda=""):
    if not ODDS_API_KEY:
        return
    ligas = {
        "9AM": ["baseball_kbo", "tennis_atp", "soccer_japan_j_league", "soccer_korea_kleague1"],
        "12PM": ["soccer_epl", "soccer_spain_la_liga", "soccer_mexico_ligamx", "soccer_uefa_champs_league"],
        "6PM": ["baseball_mlb", "basketball_nba", "americanfootball_nfl", "icehockey_nhl"],
        "12AM": ["basketball_nba", "baseball_mlb", "soccer_mexico_ligamx", "mma_mixed_martial_arts"]
    }
    deportes = ligas.get(ronda, ["baseball_mlb","soccer_mexico_ligamx","basketball_nba"])
    todos = []
    try:
        for dep in deportes:
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{dep}/odds/?apiKey={ODDS_API_KEY}&regions=us,mx&markets=h2h,spreads,totals&oddsFormat=american"
                r = requests.get(url, timeout=12).json()
                if isinstance(r, list):
                    for juego in r[:8]:
                        juego['deporte_detectado'] = dep
                        juego['ronda'] = ronda
                        todos.append(juego)
                time.sleep(1)
            except:
                continue
        with open(MOMIOS_FILE,'w',encoding='utf-8') as f:
            json.dump({"fecha": str(datetime.now(ZONA_GDL)), "ronda": ronda, "total": len(todos), "momios": todos}, f, indent=2, ensure_ascii=False)
        print(f"ESCANEO {ronda}: {len(todos)} juegos")
    except Exception as e:
        print(f"Error ojo: {e}")

@app.route('/')
def home():
    size = os.path.getsize(CHAT_FILE) if os.path.exists(CHAT_FILE) else 0
    clientes = len(cargar_clientes())
    hora = datetime.now(ZONA_GDL).strftime("%Y-%m-%d %H:%M:%S")
    return f"<html><body style='background:black;color:#00ff00;padding:20px;text-align:center'><h1>RARC TIPS - BOT + BAUL ETERNO OK</h1><p>Hora GDL: {hora}</p><p>Clientes: {clientes} | Memoria: {size}</p></body></html>"

@app.route('/healthz')
def healthz():
    return "OK", 200

@app.route('/momios')
def momios():
    escanear_ahorro("MANUAL")
    if os.path.exists(MOMIOS_FILE):
        return jsonify(json.load(open(MOMIOS_FILE,'r',encoding='utf-8')))
    return jsonify({"error": "Sin datos"})

@app.route('/api/guardar_todo',methods=['POST'])
def guardar_todo():
    try:
        data=request.get_json(force=True)
        with open(CHAT_FILE,'a',encoding='utf-8') as f:
            f.write(f"\n[{datetime.now(ZONA_GDL)}] AUTOR:{data.get('autor','')} MENSAJE:{data.get('mensaje','')}\n")
        if data.get('imagen_base64'):
            try:
                formato = data.get('formato','png').lower()
                ts = datetime.now(ZONA_GDL).strftime('%Y%m%d_%H%M%S_%f')
                ruta = f"memoria_eterna/chat/{ts}.{formato}"
                with open(ruta,"wb") as out:
                    out.write(base64.b64decode(data['imagen_base64']))
            except Exception as e:
                print(e)
        return jsonify({"status":"GUARDADO"})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/contexto_para_reina')
def contexto_para_reina():
    historial=open(CHAT_FILE,'r',encoding='utf-8').read()[-80000:] if os.path.exists(CHAT_FILE) else ""
    return jsonify({"historial":historial,"hora_gdl":str(datetime.now(ZONA_GDL)), "clientes": cargar_clientes()})

def reloj_4_rondas_gdl():
    while True:
        try:
            ahora = datetime.now(ZONA_GDL)
            hora = ahora.hour
            fecha = ahora.strftime("%Y-%m-%d")
            control = json.load(open(CONTROL_FILE,'r',encoding='utf-8')) if os.path.exists(CONTROL_FILE) else {"ultima_fecha": "", "ultima_hora_escaneada": -1}
            debe = False
            ronda = ""
            if hora == 9 and (control.get("ultima_fecha")!= fecha or control.get("ultima_hora_escaneada")!= 9):
                debe=True; ronda="9AM"
            elif hora == 12 and (control.get("ultima_fecha")!= fecha or control.get("ultima_hora_escaneada")!= 12):
                debe=True; ronda="12PM"
            elif hora == 18 and (control.get("ultima_fecha")!= fecha or control.get("ultima_hora_escaneada")!= 18):
                debe=True; ronda="6PM"
            elif hora == 0 and (control.get("ultima_fecha")!= fecha or control.get("ultima_hora_escaneada")!= 0):
                debe=True; ronda="12AM"
            if debe:
                escanear_ahorro(ronda)
                with open(CONTROL_FILE,'w',encoding='utf-8') as f:
                    json.dump({"ultima_fecha": fecha, "ultima_hora_escaneada": hora, "ronda": ronda}, f)
            time.sleep(60)
        except:
            time.sleep(60)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def run_bot():
    if bot:
        try:
            bot.infinity_polling()
        except:
            time.sleep(5)
            run_bot()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=reloj_4_rondas_gdl,daemon=True).start()
    run_bot()
