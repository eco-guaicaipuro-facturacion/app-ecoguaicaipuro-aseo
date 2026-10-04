import os
from supabase import create_client, Client
import streamlit as st

# Intentar obtener credenciales desde st.secrets (Streamlit Cloud) o variables de entorno (.env local)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znmpeopnxrgofbyrtih.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Faltan las credenciales de Supabase (SUPABASE_URL o SUPABASE_KEY). Configúrelas en los Secrets de Streamlit Cloud o en el archivo .env.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_usuarios():
    try:
        response = supabase.table("usuarios").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_usuarios: {e}")
        return []

def get_suscriptores():
    try:
        response = supabase.table("suscriptores_inmuebles").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_suscriptores: {e}")
        return []

def get_tarifas():
    try:
        response = supabase.table("tarifas_aseo").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_tarifas: {e}")
        return []

def get_facturacion():
    try:
        response = supabase.table("facturacion_historial").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error en get_facturacion: {e}")
        return []

def registrar_factura(data):
    try:
        response = supabase.table("facturacion_historial").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error en registrar_factura: {e}")
        return None

def registrar_auditoria_db(cedula, rol, accion, detalle):
    try:
        data = {
            "cedula": str(cedula),
            "rol": str(rol),
            "accion": str(accion),
            "detalle": str(detalle)
        }
        supabase.table("auditoria").insert(data).execute()
    except Exception as e:
        print(f"Error en auditoría: {e}")
