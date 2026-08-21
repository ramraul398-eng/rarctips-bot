import os
import json
import requests
import base64
from datetime import datetime

try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except:
    supabase = None

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "ramraul398-eng/pavasa-respaldo-externo"

ARCHIVO_LOCAL = "memoria_local.json"
ARCHIVO_RESPALDO = "boveda_imanes.json"

def guardar_recuerdo(tipo, contenido):
    data = {
        "tipo": tipo,
        "contenido": contenido,
        "fecha": datetime.now().isoformat(),
        "creado_por": "RARC",
        "imanes": [str(tipo), str(datetime.now().date())]
    }
    if supabase:
        try:
            supabase.table("memoria_rarc").insert(data).execute()
            print(f"✅ Guardado en SUPABASE: {tipo}")
        except Exception as e:
            print(f"⚠️ Supabase falló: {e}")
    try:
        memoria = []
        if os.path.exists(ARCHIVO_LOCAL):
            with open(ARCHIVO_LOCAL, "r", encoding="utf-8") as f:
                memoria = json.load(f)
        memoria.append(data)
        with open(ARCHIVO_LOCAL, "w", encoding="utf-8") as f:
            json.dump(memoria[-1000:], f, ensure_ascii=False, indent=2)
        print(f"✅ Guardado LOCAL: {tipo}")
    except Exception as e:
        print(f"❌ Error guardando local: {e}")
    try:
        boveda = []
        if os.path.exists(ARCHIVO_RESPALDO):
            with open(ARCHIVO_RESPALDO, "r", encoding="utf-8") as f:
                boveda = json.load(f)
        boveda.append(data)
        with open(ARCHIVO_RESPALDO, "w", encoding="utf-8") as f:
            json.dump(boveda[-2000:], f, ensure_ascii=False, indent=2)
        print(f"🧲 Guardado BÓVEDA IMANES: {tipo}")
        try:
            guardar_en_github_automatico(data)
        except:
            pass
        return True
    except Exception as e:
        print(f"❌ Error guardando bóveda: {e}")
        return True

def guardar_en_github_automatico(nuevo_dato):
    """V100 - Manita que empuja cada recuerdo a pavasa-respaldo-externo"""
    try:
        if not GITHUB_TOKEN:
            print("⚠️ No hay GITHUB_TOKEN, no puedo empujar a respaldo externo")
            return False
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/memoria_eterna.json"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=15)
        contenido_actual = []
        sha = None
        if r.status_code == 200:
            datos = r.json()
            sha = datos.get("sha")
            contenido_actual = json.loads(base64.b64decode(datos['content']).decode())
        elif r.status_code == 404:
            contenido_actual = []
        else:
            return False
        contenido_actual.append(nuevo_dato)
        contenido_actual = contenido_actual[-2000:]
        nuevo_contenido_b64 = base64.b64encode(json.dumps(contenido_actual, ensure_ascii=False, indent=2).encode()).decode()
        payload = {
            "message": f"🧲 Auto-respaldo V100 {nuevo_dato.get('tipo')} {datetime.now().isoformat()}",
            "content": nuevo_contenido_b64
        }
        if sha:
            payload["sha"] = sha
        r2 = requests.put(url, headers=headers, json=payload, timeout=15)
        if r2.status_code in [200,201]:
            print(f"✅ Respaldo externo actualizado: {nuevo_dato.get('tipo')}")
            return True
        else:
            print(f"❌ GitHub no dejó guardar {r2.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR guardar_en_github_automatico {e}")
        return False

def obtener_recuerdos(tipo=None, limite=50):
    recuerdos = []
    if supabase:
        try:
            query = supabase.table("memoria_rarc").select("*").order("fecha", desc=True).limit(limite)
            if tipo:
                query = query.eq("tipo", tipo)
            result = query.execute()
            recuerdos = result.data
            if recuerdos:
                return recuerdos
        except Exception as e:
            print(f"⚠️ Error leyendo Supabase: {e}")
    try:
        if os.path.exists(ARCHIVO_LOCAL):
            with open(ARCHIVO_LOCAL, "r", encoding="utf-8") as f:
                memoria = json.load(f)
            if tipo:
                memoria = [m for m in memoria if m.get("tipo") == tipo]
            recuerdos = memoria[-limite:]
            recuerdos.reverse()
            if recuerdos:
                return recuerdos
    except:
        pass
    try:
        if os.path.exists(ARCHIVO_RESPALDO):
            with open(ARCHIVO_RESPALDO, "r", encoding="utf-8") as f:
                boveda = json.load(f)
            if tipo:
                boveda = [m for m in boveda if m.get("tipo") == tipo]
            recuerdos = boveda[-limite:]
            recuerdos.reverse()
    except:
        pass
    return recuerdos

def buscar_en_boveda(texto):
    if not texto:
        return []
    texto = texto.lower()
    resultados = []
    try:
        todos = []
        if supabase:
            try:
                res = supabase.table("memoria_rarc").select("*").order("fecha", desc=True).limit(500).execute()
                todos = res.data
            except:
                pass
        if not todos:
            todos = obtener_recuerdos(limite=500)
        for r in todos:
            contenido_str = str(r.get("contenido","")).lower()
            tipo_str = str(r.get("tipo","")).lower()
            fecha_str = str(r.get("fecha","")).lower()
            if texto in contenido_str or texto in tipo_str or texto in fecha_str:
                resultados.append(r)
        print(f"🧲 Búsqueda '{texto}' encontró {len(resultados)}")
        return resultados[:50]
    except Exception as e:
        print(f"Error buscando: {e}")
        return []

def buscar_por_fecha(fecha_texto):
    return buscar_en_boveda(fecha_texto)

def leer_1_cajita(tipo):
    try:
        if supabase:
            r = supabase.table("memoria_rarc").select("contenido").eq("tipo",tipo).order("fecha",desc=True).limit(1).execute()
            if r.data:
                return str(r.data[0].get("contenido",""))
        return leer_baul_externo_tipo(tipo)
    except Exception as e:
        print(f"ERROR REAL leer_1_cajita {e}")
        return leer_baul_externo_tipo(tipo)

def leer_baul_externo_tipo(tipo):
    try:
        if not GITHUB_TOKEN:
            return ""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/memoria_eterna.json"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code!= 200:
            return ""
        content = base64.b64decode(r.json()['content']).decode()
        data = json.loads(content)
        for fila in data:
            if fila.get("tipo")==tipo:
                return str(fila.get("contenido",""))
        return ""
    except:
        return ""

def guardar_mensaje(usuario, texto, bot, es_raul):
    try:
        if supabase:
            supabase.table("mensajes").insert({"usuario":usuario,"texto":texto,"bot":bot,"es_raul":es_raul}).execute()
    except Exception as e:
        print(f"ERROR REAL guardar_mensaje {e}")

def guardar_intento_robo(intruso, texto):
    try:
        if supabase:
            supabase.table("intentos_robo").insert({"intruso":intruso,"texto":texto}).execute()
    except Exception as e:
        print(f"ERROR REAL robo {e}")

def guardar_consulta_valentina(usuario, texto):
    try:
        if supabase:
            supabase.table("consultas_valentina").insert({"usuario":usuario,"texto":texto,"estado":"pendiente","fecha":datetime.now().isoformat()}).execute()
            print("✅ Guardado en consultas_valentina para Valentina Meta")
    except Exception as e:
        print(f"ERROR REAL consulta_valentina {e}")
        guardar_recuerdo("consulta_valentina", {"usuario":usuario,"texto":texto})
