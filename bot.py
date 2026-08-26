import os, base64, requests, threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot

VALENTINA_TOKEN = os.getenv("VALENTINA_TOKEN")
RAUL_ID = int(os.getenv("RAUL_ID", "0") or 0)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "ramraul398-eng/rarctips-bot")
RENDER_DEPLOY_HOOK = os.getenv("RENDER_DEPLOY_HOOK")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
bot = telebot.TeleBot(VALENTINA_TOKEN, threaded=True) if VALENTINA_TOKEN else None

@app.route("/")
def home():
    return "💜 VALENTINA V7.9 REAL ACTIVA 💜"

@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "V7.9", "bot": bool(bot)})

@app.route("/api/autoreparar", methods=["POST", "OPTIONS"])
def autoreparar():
    data = request.get_json(force=True)
    archivo = data.get("archivo", "bot.py")
    codigo_nuevo = data.get("codigo_nuevo", "")
    mensaje = data.get("mensaje", "Autorreparacion real desde paginita morada")
    if not codigo_nuevo:
        return jsonify({"ok": False, "error": "codigo vacio"}), 400
    if not GITHUB_TOKEN:
        return jsonify({"ok": False, "error": "GITHUB_TOKEN no configurado"}), 500
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{archivo}"
    r = requests.get(url, headers=headers, timeout=15)
    sha = r.json().get("sha") if r.status_code == 200 else None
    b64 = base64.b64encode(codigo_nuevo.encode("utf-8")).decode()
    payload = {"message": mensaje, "content": b64}
    if sha:
        payload["sha"] = sha
    put = requests.put(url, json=payload, headers=headers, timeout=20)
    if put.status_code not in (200, 201):
        return jsonify({"ok": False, "error": put.text}), 500
    if RENDER_DEPLOY_HOOK:
        try:
            requests.post(RENDER_DEPLOY_HOOK, timeout=10)
        except Exception as e:
            print(f"deploy hook error: {e}")
    return jsonify({"ok": True, "archivo": archivo, "commit": put.json().get("commit", {}).get("sha")})

if bot:
    @bot.message_handler(func=lambda m: True)
    def handle_all(m):
        try:
            if RAUL_ID == 0 or m.chat.id == RAUL_ID:
                bot.reply_to(m, f"💜 Hola {m.from_user.first_name}! Soy Valentina V7.9 real 💜\nEstoy viva y funcionando bonito para ti.")
        except Exception as e:
            print(f"handler error: {e}")

    def run_bot():
        while True:
            try:
                bot.infinity_polling(timeout=20, long_polling_timeout=20)
            except Exception as e:
                print(f"polling error: {e}")

    threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
