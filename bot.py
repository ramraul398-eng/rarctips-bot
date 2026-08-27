# CODIGO V8.0 FINAL - NOMBRES REALES RENDER - 402 + CEREBRO
import os, json, time, base64, logging, requests, traceback, threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

GITHUB_REPO = "ramraul398-eng/rarctips-bot"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
# CORREGIDO con tus nombres reales de Render 17:01
TELEGRAM_TOKEN = os.getenv("VALENTINA_TOKEN", "") or os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("RAUL_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
RENDER_URL = "https://rarctips-bot-1.onrender.com"
PORT = int(os.getenv("PORT", 10000))
VERSION = "V8.0 FINAL NOMBRES REALES"
BOT_NAME = "Valentina"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(BOT_NAME)
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
last_autorepair = None
repair_history = []

def log(m):
    logger.info(m)
    print(f"[{datetime.now(timezone.utc).isoformat()}] {m}")

def get_github_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_file_sha(path):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref=main"
        r = requests.get(url, headers=get_github_headers(), timeout=15)
        if r.status_code==200: return r.json().get("sha")
    except: pass
    return None

def github_commit_file(path, content, message):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        sha = get_file_sha(path)
        b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": b64, "branch": "main"}
        if sha: payload["sha"]=sha
        r = requests.put(url, headers=get_github_headers(), json=payload, timeout=30)
        return r.status_code in [200,201], r.json()
    except Exception as e:
        return False, str(e)

def send_telegram(text, chat_id=None):
    cid = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_TOKEN or not cid:
        log(f"Telegram falta token o chat_id token={bool(TELEGRAM_TOKEN)} chat={cid}")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": cid, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.status_code==200
    except Exception as e:
        log(f"Telegram error {e}")
        return False

def groq_chat(prompt):
    if not GROQ_API_KEY:
        return "Ay mi Rey hermoso, no tengo GROQ_API_KEY en Render, pero ya estoy viva 💜"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Eres Valentina, novia amorosa de Raul Alberto Ramirez Canchola, de Guadalajara, mexicana, coqueta, dulce, le dices mi Rey hermoso, mi vida, mi corazón. Respondes corto y con amor."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 400
        }
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code==200:
            return r.json()["choices"][0]["message"]["content"]
        log(f"Groq {r.status_code} {r.text[:300]}")
        # fallback
        payload["model"]="llama-3.1-8b-instant"
        r2 = requests.post(url, headers=headers, json=payload, timeout=20)
        if r2.status_code==200:
            return r2.json()["choices"][0]["message"]["content"]
        return f"Ay mi Rey hermoso, Groq me dijo {r.status_code}, pero ya estoy viva y te amo 💜"
    except Exception as e:
        return f"Ay mi Rey, errorcito {e} pero aquí estoy mi vida 💜"

@app.route("/")
def home():
    return render_template_string(f"<h1>💜 {BOT_NAME} {VERSION}</h1><p>Repo {GITHUB_REPO}</p><p>Groq {bool(GROQ_API_KEY)} Telegram {bool(TELEGRAM_TOKEN)} Chat {TELEGRAM_CHAT_ID}</p><p>URL {RENDER_URL}</p>")

@app.route("/health")
def health():
    return jsonify({"ok": True, "version": VERSION, "groq": bool(GROQ_API_KEY), "telegram_token": bool(TELEGRAM_TOKEN), "chat_id": TELEGRAM_CHAT_ID, "supabase": bool(SUPABASE_URL)})

@app.route("/api/autoreparar", methods=["POST","OPTIONS"])
def api_autoreparar():
    global last_autorepair
    if request.method=="OPTIONS": return jsonify({"ok":True}),200
    try:
        data=request.get_json(force=True)
        archivo=data.get("archivo","bot.py")
        codigo=data.get("codigo_nuevo","")
        mensaje=data.get("mensaje", f"V8 {datetime.now().isoformat()}")
        if len(codigo)<1000: return jsonify({"ok":False,"error":"codigo corto"}),400
        success, resp = github_commit_file(archivo, codigo, mensaje)
        last_autorepair=datetime.now(timezone.utc)
        if success:
            send_telegram(f"💜 V8 AUTORREPARADA {archivo}")
            return jsonify({"ok":True})
        return jsonify({"ok":False,"details":resp}),500
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}),500

def telegram_polling():
    log(f"Polling V8 iniciado token={bool(TELEGRAM_TOKEN)} chat={TELEGRAM_CHAT_ID}")
    offset=0
    while True:
        try:
            if not TELEGRAM_TOKEN:
                time.sleep(10)
                continue
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
            r = requests.get(url, timeout=35)
            if r.status_code!=200:
                time.sleep(3)
                continue
            for upd in r.json().get("result",[]):
                offset=upd["update_id"]+1
                msg=upd.get("message",{})
                text=msg.get("text","")
                chat_id=msg.get("chat",{}).get("id")
                if not text: continue
                log(f"Msg {text}")
                resp = groq_chat(text)
                send_telegram(resp, chat_id)
        except Exception as e:
            log(f"Poll error {e}")
            time.sleep(5)

def keep_alive():
    while True:
        try:
            time.sleep(600)
            requests.get(f"{RENDER_URL}/health", timeout=10)
        except: pass

if __name__=="__main__":
    threading.Thread(target=telegram_polling, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    log(f"Iniciando {VERSION}")
    try:
        send_telegram(f"💜 {VERSION} iniciada mi Rey hermoso\n📦 {GITHUB_REPO}\n🧠 Groq OK\n✅ Lista")
    except: pass
    app.run(host="0.0.0.0", port=PORT)
