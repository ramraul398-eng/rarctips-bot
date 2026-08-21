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

# === 1. MEMORIA ETERNA - LO QUE NUNCA SE OLVIDA (9 filas) ===
def guardar_recuerdo(clave, contenido):
    """Guarda en memoria_eterna (clave/valor) - ORIGINAL SIEMPRE SE QUEDA"""
    data_eterna = {
        "clave": str(clave),
        "valor": json.dumps(contenido, ensure_ascii=False) if isinstance(contenido, dict) else str(contenido)
    }
    # Para compatibilidad con tu estructura vieja
    data_log = {
        "tipo": str(clave),
        "contenido": contenido,
        "fecha": datetime.now().isoformat(),
        "creado_por": "RARC",
        "imanes": [str(clave), str(datetime.now().date())]
    }
    if supabase:
        try:
            # GUARDA EN TU TABLA REAL QUE SI EXISTE
            supabase.table("memoria_eterna").upsert(data_eterna, on_conflict="clave").execute()
            print(f"✅ Guardado en memoria_eterna: {clave}")
            # Tambien guarda en boveda
            try:
                supabase.table("memoria_boveda").insert({
                    "valor": data_eterna["valor"],
                    "descripcion": str(clave),
                    "creado_en": datetime.now().isoformat()
                }).execute()
            except:
                pass
        except Exception as e:
            print(f"⚠️ Supabase memoria_eterna falló: {e}")

    # LOCAL Y BOVEDA + GITHUB (respaldo)
    try:
        memoria = []
        if os.path.exists(ARCHIVO_LOCAL):
            with open(ARCHIVO_LOCAL, "r", encoding="utf-8") as f:
                memoria = json.load(f)
        memoria.append(data_log)
        with open(ARCHIVO_LOCAL, "w", encoding="utf-8") as f:
            json.dump(memoria[-1000:], f, ensure_ascii=False, indent=2)
    except:
        pass
    try:
        boveda = []
        if os.path.exists(ARCHIVO_RESPALDO):
            with open(ARCHIVO_RESPALDO, "r", encoding="utf-8") as f:
                boveda = json.load(f)
        boveda.append(data_log)
        with open(ARCHIVO_RESPALDO, "w", encoding="utf-8") as f:
            json.dump(boveda[-2000:], f, ensure_ascii=False, indent=2)
        try:
            guardar_en_github_automatico(data_log)
        except:
            pass
    except:
        pass
    return True

def guardar_en_github_automatico(nuevo_dato):
    try:
        if not GITHUB_TOKEN:
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
        contenido_actual.append(nuevo_dato)
        contenido_actual = contenido_actual[-2000:]
        nuevo_contenido_b64 = base64.b64encode(json.dumps(contenido_actual, ensure_ascii=False, indent=2).encode()).decode()
        payload = {"message": f"🧲 Auto-respaldo V101 {nuevo_dato.get('tipo')} {datetime.now().isoformat()}", "content": nuevo_contenido_b64}
        if sha:
            payload["sha"] = sha
        r2 = requests.put(url, headers=headers, json=payload, timeout=15)
        return r2.status_code in [200,201]
    except Exception as e:
        print(f"❌ ERROR github {e}")
        return False

def obtener_recuerdos(clave=None, limite=50):
    """LEE DE memoria_eterna - entrada directa a lo que ya hay"""
    recuerdos = []
    if supabase:
        try:
            query = supabase.table("memoria_eterna").select("*").limit(limite)
            if clave:
                query = query.eq("clave", clave)
            result = query.execute()
            recuerdos = result.data
            if recuerdos:
                # Convierte a formato viejo para compatibilidad
                recuerdos_compat = []
                for r in recuerdos:
                    try:
                        cont = json.loads(r.get("valor",""))
                    except:
                        cont = r.get("valor","")
                    recuerdos_compat.append({"tipo": r.get("clave"), "contenido": cont, "fecha": ""})
                return recuerdos_compat
        except Exception as e:
            print(f"⚠️ Error leyendo memoria_eterna: {e}")
    return recuerdos

def buscar_en_boveda(texto):
    if not texto:
        return []
    texto = texto.lower()
    resultados = []
    try:
        todos = obtener_recuerdos(limite=200)
        for r in todos:
            contenido_str = str(r.get("contenido","")).lower()
            tipo_str = str(r.get("tipo","")).lower()
            if texto in contenido_str or texto in tipo_str:
                resultados.append(r)
        # Tambien busca en charlas_eternas
        if supabase:
            try:
                res = supabase.table("charlas_eternas").select("*").order("created_at", desc=True).limit(200).execute()
                for c in res.data:
                    if texto in str(c.get("mensaje","")).lower():
                        resultados.append({"tipo": "charla", "contenido": c.get("mensaje"), "quien": c.get("quien")})
            except:
                pass
        print(f"🧲 Búsqueda '{texto}' encontró {len(resultados)}")
        return resultados[:50]
    except Exception as e:
        print(f"Error buscando: {e}")
        return []

# === 2. CHARLAS ETERNAS - CAJITA DONDE GUARDA TODO LO QUE ESCUCHA ===
def guardar_mensaje(quien, mensaje, resumen_corto=""):
    """Guarda en charlas_eternas - pum pum pum todo lo de Meta y Telegram - COPIA, ORIGINAL SE QUEDA"""
    try:
        if supabase:
            supabase.table("charlas_eternas").insert({
                "quien": str(quien),
                "mensaje": str(mensaje),
                "resumen_corto": str(resumen_corto)[:200]
            }).execute()
            print(f"✅ Mensaje guardado en charlas_eternas de {quien}")
            return True
    except Exception as e:
        print(f"ERROR REAL guardar_mensaje charlas_eternas {e}")
        return False

def guardar_en_historial_infinito(tipo, quien, mensaje, archivo_url="", plataforma="meta_telegram"):
    """Para imagenes, HTML, tablitas, graficas - separa por tipo"""
    try:
        if supabase:
            supabase.table("historial_infinito").insert({
                "tipo": str(tipo), # imagen, html, tabla, grafica, texto
                "quien": str(quien),
                "mensaje": str(mensaje),
                "archivo_url": str(archivo_url)
            }).execute()
            print(f"✅ Guardado en historial_infinito tipo={tipo}")
            return True
    except Exception as e:
        print(f"ERROR historial_infinito {e}")
        return False

def buscar_archivo(texto_busqueda, tipo=None):
    """BUSCA COPIA - original siempre se queda en bodega imagenes/videos/gifs/audios"""
    try:
        if supabase:
            query = supabase.table("historial_infinito").select("*").order("created_at", desc=True).limit(100)
            if tipo:
                query = query.eq("tipo", tipo)
            res = query.execute()
            resultados = []
            for r in res.data:
                if texto_busqueda.lower() in str(r.get("mensaje","")).lower() or texto_busqueda.lower() in str(r.get("archivo_url","")).lower():
                    resultados.append(r)
            return resultados
    except Exception as e:
        print(f"ERROR buscar_archivo {e}")
    return []

# === FUNCIONES VIEJAS PARA COMPATIBILIDAD CON BOT.PY ===
def leer_1_cajita(clave):
    rec = obtener_recuerdos(clave=clave, limite=1)
    if rec:
        return str(rec[0].get("contenido",""))
    return ""

def buscar_por_fecha(fecha_texto):
    return buscar_en_boveda(fecha_texto)

def guardar_intento_robo(intruso, texto):
    return guardar_en_historial_infinito("intento_robo", intruso, texto)

def guardar_consulta_valentina(usuario, texto):
    return guardar_mensaje(f"consulta_valentina_{usuario}", texto, "consulta para Valentina Meta")
