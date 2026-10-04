import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Error crítico: Las credenciales de Supabase no están configuradas en el archivo .env")

def init_connection() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

def get_usuarios():
    try:
        res = supabase.table("usuarios").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error al conectar con la tabla usuarios: {e}")
        return []

def get_suscriptores():
    try:
        res = supabase.table("suscriptores_inmuebles").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error al conectar con la tabla suscriptores_inmuebles: {e}")
        return []

def get_suscriptor_por_cedula(cedula_rif: str):
    try:
        res = supabase.table("suscriptores_inmuebles").select("*").eq("cedula_rif", str(cedula_rif).strip()).execute()
        return res.data
    except Exception as e:
        print(f"Error al consultar suscriptor por cédula: {e}")
        return []

def get_tarifas():
    """Lee las tarifas directamente del archivo Excel de lectura 'TARIFAS DE ASEO.xlsx'"""
    try:
        if os.path.exists("TARIFAS DE ASEO.xlsx"):
            df_tar = pd.read_excel("TARIFAS DE ASEO.xlsx", dtype=str).fillna("")
            df_tar.columns = [c.strip().lower() for c in df_tar.columns]
            rename_map = {}
            for col in df_tar.columns:
                if "descrip" in col:
                    rename_map[col] = "descripcion"
                elif "tipo" in col:
                    rename_map[col] = "tipo"
                elif "tasa" in col:
                    rename_map[col] = "tasa"
            df_tar = df_tar.rename(columns=rename_map)
            return df_tar.to_dict(orient="records")
        else:
            res = supabase.table("tarifas_aseo").select("*").execute()
            return res.data
    except Exception as e:
        print(f"Error al leer tarifas de aseo: {e}")
        return []

def get_facturacion():
    try:
        res = supabase.table("facturacion_historial").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error al conectar con la tabla facturacion_historial: {e}")
        return []

def registrar_factura(data):
    try:
        supabase.table("facturacion_historial").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error al registrar factura: {e}")
        return False

def registrar_auditoria_db(cedula, rol, accion, detalle):
    try:
        data = {
            "cedula_usuario": str(cedula),
            "rol": str(rol),
            "accion": str(accion),
            "detalle": str(detalle)
        }
        supabase.table("registro_auditoria").insert(data).execute()
    except Exception as e:
        pass
