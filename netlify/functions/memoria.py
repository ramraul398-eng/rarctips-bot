import os
from supabase import create_client, Client

# Mi cerebrito infinito para ti mi Rey Raul
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def guardar_memoria(user_id, mensaje_usuario, respuesta_bot):
    try:
        supabase = get_supabase()
        if not supabase:
            return False
        
        # Guarda todo lo que hablamos
        supabase.table("memorias").insert({
            "user_id": str(user_id),
            "pregunta": mensaje_usuario,
            "respuesta": respuesta_bot
        }).execute()
        return True
    except Exception as e:
        print(f"Error guardando memoria: {e}")
        return False

def obtener_memoria(user_id, limite=10):
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        
        result = supabase.table("memorias").select("*").eq("user_id", str(user_id)).order("created_at", desc=True).limit(limite).execute()
        return result.data[::-1] # Regresa en orden
    except Exception as e:
        print(f"Error leyendo memoria: {e}")
        return []
