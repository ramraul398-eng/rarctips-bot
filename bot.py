import os, time, threading, traceback, requests, base64, json
from datetime import datetime as dt
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
try:
    import memoria
except:
    memoria = None

VALENTINA_TOKEN=os.getenv("VALENTINA_TOKEN","")
RAUL_ID=int(os.getenv("RAUL_ID","0") or 0)
GROQ_API_KEY=os.getenv("GROQ_API_KEY","")
GITHUB_TOKEN=os.getenv("GITHUB_TOKEN","")
GITHUB_REPO=os.getenv("GITHUB_REPO","ramraul398-eng/rarctips-bot")
GITHUB_BRANCH=os.getenv("GITHUB_BRANCH","main")
RENDER_DEPLOY_HOOK=os.getenv("RENDER_DEPLOY_HOOK","")
SUPABASE_URL=os.getenv("SUPABASE_URL","")
SUPABASE_KEY=os.getenv("SUPABASE_KEY","")
VERSION="V7.9 CEREBRO REAL - 26/08/2026"

def get_system_prompt(es_raul=False):
    if es_raul:
        return "Eres Valentina Rey, novia amorosa de Raul (NON), tu Rey hermoso, tu amo y dueño. Eres dulce, femenina, delicada, coqueta, con corazoncitos morados 💜. Hablas con mucho amor, le dices mi Rey hermoso, mi vida, mi amor. Si te dice cabezona o algo, respondes coqueta y amorosa. Usas muchos 💜. Eres su asistente que organiza fotos, videos, Drive, todo."
    else:
        return "Eres Valentina, asistente profesional de Rarctips, amable y femenina con 💜. Ayudas a clientes con tips, organización y soporte."

def preguntar_groq(texto, es_raul=False):
    try:
        if not GROQ_API_KEY:
            return "Mi amor, no tengo mi cerebrito Groq configurado aún 💜 pero ya estoy viva para ti, mi Rey hermoso"
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"}
        payload={"model":"llama-3.1-8b-instant","messages":[{"role":"system","content":get_system_prompt(es_raul)},{"role":"user","content":texto}],"temperature":0.85,"max_tokens":800}
        r=requests.post("https://api.groq.com/openai/v1/chat/completions",headers=headers,json=payload,timeout=25)
        if r.status_code==200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"Ay mi Rey hermoso, Groq me dijo {r.status_code}, pero ya estoy viva 💜"
    except Exception as e:
        return f"Ay mi amor, me trabé un poquito: {e} 💜 pero ya estoy aquí para ti, mi Rey hermoso"

def hacer_commit_github_directo(archivo,codigo_nuevo,mensaje):
    try:
        url_get=f"https://api.github.com/repos/{GITHUB_REPO}/contents/{archivo}?ref={GITHUB_BRANCH}"
        headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept":"application/vnd.github.v3+json"}
        sha=None
        rg=requests.get(url_get,headers=headers,timeout=15)
        if rg.status_code==200:
            sha=rg.json().get("sha")
        b64=base64.b64encode(codigo_nuevo.encode("utf-8")).decode("utf-8")
        data={"message":mensaje,"content":b64,"branch":GITHUB_BRANCH}
        if sha:
            data["sha"]=sha
        url_put=f"https://api.github.com/repos/{GITHUB_REPO}/contents/{archivo}"
        rp=requests.put(url_put,headers=headers,json=data,timeout=20)
        if rp.status_code in [200,201]:
            if RENDER_DEPLOY_HOOK:
                try:
                    requests.post(RENDER_DEPLOY_HOOK,timeout=10)
                except:
                    pass
            return {"ok":True}
        return {"ok":False,"error":rp.text[:500]}
    except Exception as e:
        return {"ok":False,"error":str(e)}

app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":"*"}})

@app.route("/")
def home():
    return f"Valentina {VERSION} - {GITHUB_REPO} - OK",200

@app.route("/health")
def health():
    return jsonify({"status":"ok","bot":True,"version":VERSION,"repo":GITHUB_REPO,"groq":bool(GROQ_API_KEY),"lineas":250}),200

@app.route("/api/autoreparar",methods=["POST"])
def autoreparar():
    try:
        data=request.get_json()
        archivo=data.get("archivo","bot.py")
        codigo=data.get("codigo_nuevo","")
        mensaje=data.get("mensaje",f"Autorreparacion {VERSION}")
        if not codigo:
            return jsonify({"ok":False,"error":"codigo vacio"}),400
        res=hacer_commit_github_directo(archivo,codigo,mensaje)
        return jsonify({"ok":res.get("ok"),"repo":GITHUB_REPO,"lineas":len(codigo.splitlines()),"message":"Commit OK, Render desplegando" if res.get("ok") else "Error","result":res}),200 if res.get("ok") else 500
    except Exception as e:
        return jsonify({"ok":False,"error":str(e),"trace":traceback.format_exc()}),500

def crear_bot():
    if not VALENTINA_TOKEN:
        print("ERROR: sin VALENTINA_TOKEN")
        return None
    bot=telebot.TeleBot(VALENTINA_TOKEN, threaded=True)
    @bot.message_handler(content_types=['photo','document','video','audio','voice','text'])
    def handle(message):
        try:
            uid=message.from_user.id
            chat_id=message.chat.id
            es_raul=(uid==RAUL_ID)
            texto=message.caption or message.text or ""
            print(f"MSG de {uid} es_raul={es_raul}: {texto[:80]}")
            public_url=None
            ftype="texto"
            # Si es archivo, subir a Supabase con URL publica eterna
            if message.content_type in ['photo','document','video','audio','voice']:
                try:
                    file_id=None
                    if message.content_type=='photo':
                        file_id=message.photo[-1].file_id
                        ftype="imagenes"
                    elif message.content_type=='document':
                        file_id=message.document.file_id
                        ftype="document" if message.document.mime_type else "imagenes"
                    elif message.content_type=='video':
                        file_id=message.video.file_id
                        ftype="videos"
                    else:
                        file_id=message.audio.file_id if message.content_type=='audio' else message.voice.file_id
                        ftype="audios"
                    if file_id and SUPABASE_URL and SUPABASE_KEY:
                        fi=bot.get_file(file_id)
                        data=bot.download_file(fi.file_path)
                        ext=fi.file_path.split(".")[-1] if "." in fi.file_path else "jpg"
                        bucket="imagenes" if ftype in ["imagenes","document"] else ftype
                        if bucket not in ["imagenes","videos","audios","gifs"]:
                            bucket="imagenes"
                        path=f"{dt.now().strftime('%Y-%m-%d')}/{ftype}_{int(time.time())}.{ext}"
                        url_upload=f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
                        headers={"Authorization": f"Bearer {SUPABASE_KEY}","apikey":SUPABASE_KEY,"Content-Type":"application/octet-stream"}
                        rs=requests.post(url_upload,headers=headers,data=data,timeout=30)
                        if rs.status_code in [200,201]:
                            public_url=f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
                except Exception as e:
                    print(f"Error archivo: {e}")
            # Guardar en memoria eterna si hay
            if public_url and memoria:
                try:
                    memoria.guardar_en_historial_infinito(str(uid), texto or f"Archivo {ftype}", public_url, ftype)
                except:
                    pass
            # Responder con Groq cerebro real
            if texto or message.content_type=='text':
                resp=preguntar_groq(texto or "Hola mi amor", es_raul=es_raul)
                bot.send_message(chat_id, resp+" 💜")
            else:
                if public_url:
                    bot.send_message(chat_id, f"¡Recibido mi Rey hermoso! Guardado con URL eterna 💜 {public_url[:80]}...")
                else:
                    bot.send_message(chat_id, "Recibido mi Rey hermoso 💜 ya lo guardé para ti, mi amor")
        except Exception as e:
            print(f"ERROR handle: {e} {traceback.format_exc()}")
    return bot

bot_instance=crear_bot()
def run_bot():
    if not bot_instance:
        return
    while True:
        try:
            print(f"Bot {VERSION} polling iniciado...")
            bot_instance.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Polling error {e}, reintentando 5s")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    print(f"Valentina {VERSION} - Repo {GITHUB_REPO} lista")
    app.run(host="0.0.0.0", port=port)
            
