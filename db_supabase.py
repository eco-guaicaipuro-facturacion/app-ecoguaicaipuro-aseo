import os
from supabase import create_client, Client
import streamlit as st

SUPABASE_URL = ""
SUPABASE_KEY = ""

# Intentar leer desde st.secrets de forma flexible (plano o seccionado)
try:
    if "SUPABASE_URL" in st.secrets:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
    elif "supabase" in st.secrets and "SUPABASE_URL" in st.secrets["supabase"]:
        SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
except Exception:
    pass

try:
    if "SUPABASE_KEY" in st.secrets:
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    elif "supabase" in st.secrets and "SUPABASE_KEY" in st.secrets["supabase"]:
        SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
except Exception:
    pass

# Si no están en st.secrets, intentar entorno local (.env)
if not SUPABASE_URL or not SUPABASE_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znmpeopnxrgofbyrtih.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Faltan las credenciales de Supabase en los Secrets de Streamlit Cloud o en el archivo .env.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None
    st.error(f"⚠️ Error al inicializar cliente Supabase: {e}")

def get_usuarios():
    try:
        if not supabase: return []
        response = supabase.table("usuarios").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_usuarios: {e}")
        return []

def get_suscriptores():
    try:
        if not supabase: return []
        response = supabase.table("suscriptores_inmuebles").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_suscriptores: {e}")
        return []

def get_tarifas():
    try:
        if not supabase: return []
        response = supabase.table("tarifas_aseo").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_tarifas: {e}")
        return []

def get_facturacion():
    try:
        if not supabase: return []
        response = supabase.table("facturacion_historial").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_facturacion: {e}")
        return []

def registrar_factura(data):
    try:
        if not supabase: return None
        response = supabase.table("facturacion_historial").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error en registrar_factura: {e}")
        return None

def registrar_auditoria_db(cedula, rol, accion, detalle):
    try:
        if not supabase: return
        data = {
            "cedula": str(cedula),
            "rol": str(rol),
            "accion": str(accion),
            "detalle": str(detalle)
        }
        supabase.table("auditoria").insert(data).execute()
    except Exception as e:
        print(f"Error en auditoría: {e}")
