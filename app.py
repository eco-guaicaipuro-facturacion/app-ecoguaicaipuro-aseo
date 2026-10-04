import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# Importar funciones limpias y seguras desde db_supabase.py
from db_supabase import (
    get_usuarios, 
    get_suscriptores, 
    get_tarifas, 
    get_facturacion, 
    registrar_factura, 
    registrar_auditoria_db,
    supabase
)

st.set_page_config(
    page_title="Eco Guaicaipuro - Sistema de Gestión", 
    page_icon="♻️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

LOGO_ECO = "Eco_Guaicaipuro.png"
LOGO_GUAICAIPURO = "Guaicaipuro_Ciudad_Capital.png"

# ==========================================
# CONTROL DE SESIÓN E INACTIVIDAD (20 MIN)
# ==========================================
INACTIVITY_LIMIT = 20 * 60  # 20 minutos en segundos

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_cedula = ""
    st.session_state.user_rol = ""
    st.session_state.user_nombre = ""
    st.session_state.last_activity = time.time()
    st.session_state.ver_portal_ciudadano = False

if st.session_state.logged_in:
    tiempo_transcurrido = time.time() - st.session_state.last_activity
    if tiempo_transcurrido > INACTIVITY_LIMIT:
        st.session_state.logged_in = False
        st.warning("⚠️ Sesión expirada por inactividad (20 minutos). Por favor, inicie sesión nuevamente.")
        st.rerun()
    else:
        st.session_state.last_activity = time.time()

# ==========================================
# PANTALLA DE LOGIN / PORTAL CIUDADANO
# ==========================================
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .login-card { background: #ffffff; padding: 30px; border-radius: 15px; border: 2px solid #52b788; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 450px; margin: auto; }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(LOGO_ECO):
            st.image(LOGO_ECO, width=120)
        st.markdown("<h2 style='text-align: center; color: #1b4332;'>Eco Guaicaipuro</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Sistema de Gestión, Facturación y Cobranza (Cloud)</p>", unsafe_allow_html=True)
        
        tab_login, tab_portal = st.tabs(["🔐 Acceso Operativo", "📱 Portal Suscriptor"])
        
        with tab_login:
            with st.form("form_login"):
                cedula_ing = st.text_input("Cédula de Identidad:")
                clave_ing = st.text_input("Contraseña:", type="password")
                btn_entrar = st.form_submit_button("Ingresar al Sistema", use_container_width=True, type="primary")
                
                if btn_entrar:
                    usuarios_db = get_usuarios()
                    match = [u for u in usuarios_db if str(u.get("cedula")).strip() == cedula_ing.strip() and str(u.get("clave")).strip() == clave_ing.strip()]
                    if match:
                        row = match[0]
                        st.session_state.logged_in = True
                        st.session_state.user_cedula = str(row.get("cedula"))
                        st.session_state.user_rol = str(row.get("rol"))
                        st.session_state.user_nombre = str(row.get("nombre"))
                        st.session_state.last_activity = time.time()
                        registrar_auditoria_db(st.session_state.user_cedula, st.session_state.user_rol, "LOGIN", "Inicio de sesión exitoso")
                        st.success("✅ ¡Acceso concedido!")
                        st.rerun()
                    else:
                        st.error("❌ Cédula o contraseña incorrecta.")
            
            with st.expander("❓ ¿Olvidó su clave de Supervisor (Pregunta Secreta)?"):
                with st.form("form_pregunta"):
                    c_sup = st.text_input("Cédula de Supervisor:")
                    r_sup = st.text_input("Respuesta a Pregunta Secreta (Sombra):")
                    n_clave = st.text_input("Nueva Contraseña:", type="password")
                    btn_cambiar = st.form_submit_button("Restablecer Clave")
                    if btn_cambiar:
                        if r_sup.strip().lower() == "sombra":
                            usuarios_db = get_usuarios()
                            match_sup = [u for u in usuarios_db if str(u.get("cedula")).strip() == c_sup.strip() and str(u.get("rol")) == "Supervisor"]
                            if match_sup:
                                supabase.table("usuarios").update({"clave": n_clave.strip()}).eq("cedula", c_sup.strip()).execute()
                                st.success("✅ Clave restablecida con éxito en la nube. Ya puede iniciar sesión.")
                            else:
                                st.error("Cédula de Supervisor no encontrada.")
                        else:
                            st.error("Respuesta secreta incorrecta (Recuerde: Sombra).")

        with tab_portal:
            st.markdown("### 📱 Consulta y Reporte Ciudadano")
            st.info("Ingrese su Cédula o RIF para consultar su estado de cuenta y reportar pagos desde cualquier ubicación.")
            cedula_cli = st.text_input("Cédula / RIF del Suscriptor:", key="cli_ced_portal")
            
            if st.button("Consultar Estado de Cuenta", use_container_width=True, type="primary"):
                if cedula_cli.strip():
                    st.session_state.cedula_cliente_portal = cedula_cli.strip()
                    st.session_state.ver_portal_ciudadano = True
                else:
                    st.error("Ingrese una cédula o RIF válido.")

            if st.session_state.get("ver_portal_ciudadano", False):
                st.markdown("---")
                c_buscada = st.session_state.get("cedula_cliente_portal", "").strip()
                
                try:
                    # Consulta directa, segura y optimizada a Supabase (tolerante a mayúsculas/minúsculas y espacios)
                    res_sub = supabase.table("suscriptores_inmuebles") \
                                      .select("*") \
                                      .ilike("cedula_rif", f"%{c_buscada}%") \
                                      .execute()
                    
                    match_s = res_sub.data if res_sub.data else []
                    
                    if match_s:
                        s = match_s[0]
                        st.success(f"¡Bienvenido, {s.get('suscriptor')}!")
                        st.info(f"**Dirección/Mercado:** {s.get('direccion')} | **Código/Local:** {s.get('codigo')} | **Actividad:** {s.get('actividad_economica')}")
                        
                        st.markdown("#### 📑 Historial de Pagos y Estado de Cuenta")
                        
                        # Consultar facturas directamente en Supabase filtrando por cédula_rif o nombre comercial
                        res_fac = supabase.table("facturacion_historial") \
                                          .select("*") \
                                          .or_(f"cedula_rif.ilike.%{c_buscada}%,nombre_comercial.ilike.%{s.get('suscriptor')}%") \
                                          .execute()
                        
                        mis_facturas = res_fac.data if res_fac.data else []
                        
                        if mis_facturas:
                            st.dataframe(pd.DataFrame(mis_facturas), use_container_width=True)
                        else:
                            st.warning("No tiene pagos registrados en el sistema todavía.")
                    else:
                        st.error("❌ Cédula o RIF no encontrado en la base de datos.")
                except Exception as e:
                    st.error(f"⚠️ Error al conectar con el servidor cloud: {e}")

    st.stop()

# ==========================================
# APLICACIÓN PRINCIPAL (USUARIO AUTENTICADO)
# ==========================================
rol_actual = st.session_state.user_rol
nombre_actual = st.session_state.user_nombre

# Carga de suscriptores optimizada
suscriptores_data = get_suscriptores()
df = pd.DataFrame(suscriptores_data) if suscriptores_data else pd.DataFrame(columns=[
    "mercado", "suscriptor", "cedula_rif", "contrato", "codigo", "actividad_economica", "telefono", "correo_electronico"
])

st.markdown("""
    <style>
    .main { background-color: #f4f9f4; }
    .header-box { background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .config-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #52b788; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 Usuario: {nombre_actual}")
    st.markdown(f"**Rol:** `{rol_actual}`")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        registrar_auditoria_db(st.session_state.user_cedula, rol_actual, "LOGOUT", "Cierre de sesión")
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏛️ Identidad Institucional")
    if os.path.exists(LOGO_ECO): st.image(LOGO_ECO)
    if os.path.exists(LOGO_GUAICAIPURO): st.image(LOGO_GUAICAIPURO)

st.markdown("""
    <div class="header-box">
        <div>
            <h1 style="margin:0; font-size: 24px;">♻️ ECO GUAICAIPURO - Sistema en Línea</h1>
            <p style="margin:5px 0 0 0; font-size: 13px; opacity: 0.9;">Módulo de Fiscalización y Actualización Cloud</p>
        </div>
        <div style="font-size: 45px;">🧮📋</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("### ⚙️ Configuración del Día de Gestión")
with st.container():
    st.markdown('<div class="config-box">', unsafe_allow_html=True)
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        fecha_actual = st.date_input("Fecha de Gestión", datetime.now())
    with col_cfg2:
        tasa_dolar_bcv = st.number_input("Tasa Dólar BCV - Bs.", min_value=0.0, value=0.0, step=0.1, format="%.2f")
    st.markdown('</div>', unsafe_allow_html=True)

st.session_state.tasa_mmv_val = tasa_dolar_bcv
st.session_state.fecha_gestion = fecha_actual

if tasa_dolar_bcv <= 0.0:
    st.warning("⚠️ **Debe colocar el valor del dólar del día de la gestión.**")
    st.stop()

st.success(f"✅ Tasa Dólar BCV activa: **Bs. {tasa_dolar_bcv:,.2f}**")
st.markdown("---")

col_mercado = "mercado" if "mercado" in df.columns else df.columns[0]
col_suscriptor = "suscriptor" if "suscriptor" in df.columns else df.columns[1]
col_cedula = "cedula_rif" if "cedula_rif" in df.columns else df.columns[2]
col_actividad = "actividad_economica" if "actividad_economica" in df.columns else df.columns[3]
col_local = "codigo" if "codigo" in df.columns else df.columns[4]
col_telefono = "telefono" if "telefono" in df.columns else df.columns[5]

col1, col2 = st.columns(2)
mercados = [""] + list(df[col_mercado].dropna().unique()) if not df.empty else [""]
mercado_sel = col1.selectbox("Filtrar por Mercado:", mercados, key="filtro_mercado")

if mercado_sel and mercado_sel != "":
    suscriptores = [""] + list(df[df[col_mercado] == mercado_sel][col_suscriptor].dropna().unique())
else:
    suscriptores = [""] + list(df[col_suscriptor].dropna().unique()) if not df.empty else [""]

suscriptor_sel = col2.selectbox("Seleccionar Suscriptor:", suscriptores, key="filtro_suscriptor")

datos_actuales = {"mercado": "", "suscriptor": "", "cedula": "", "actividad": "", "local": "", "telefono": ""}

if mercado_sel and suscriptor_sel and suscriptor_sel != "":
    match = df[(df[col_mercado] == mercado_sel) & (df[col_suscriptor] == suscriptor_sel)]
    if not match.empty:
        row = match.iloc[0]
        datos_actuales = {
            "mercado": str(row.get(col_mercado, "")), "suscriptor": str(row.get(col_suscriptor, "")),
            "cedula": str(row.get(col_cedula, "")), "actividad": str(row.get(col_actividad, "")),
            "local": str(row.get(col_local, "")), "telefono": str(row.get(col_telefono, ""))
        }

if suscriptor_sel and suscriptor_sel != "":
    st.markdown("")
    if st.button("📄 Declaración y Cobro", use_container_width=True, type="primary"):
        st.session_state.datos_declaracion = datos_actuales
        st.switch_page("pages/Declaracion.py")

st.markdown("---")
st.markdown("### 📋 Formulario de Detalle y Edición")

with st.form("form_edicion"):
    c1, c2 = st.columns(2)
    with c1:
        m_val = st.text_input("1. MERCADO", value=datos_actuales["mercado"])
        s_val = st.text_input("2. SUSCRIPTOR", value=datos_actuales["suscriptor"])
        c_val = st.text_input("3. CÉDULA O RIF", value=datos_actuales["cedula"])
        a_val = st.text_input("4. ACTIVIDAD ECONÓMICA", value=datos_actuales["actividad"])
    with c2:
        n_val = st.text_input("5. NO. LOCAL / CÓDIGO", value=datos_actuales["local"])
        t_val = st.text_input("6. TELÉFONO", value=datos_actuales["telefono"])

    guardar = st.form_submit_button("💾 Guardar Cambios en la Nube", use_container_width=True)

    if guardar:
        if not s_val or not n_val:
            st.error("❌ El nombre del suscriptor y el código son obligatorios.")
        else:
            data_up = {
                "mercado": m_val,
                "suscriptor": s_val,
                "cedula_rif": c_val,
                "actividad_economica": a_val,
                "codigo": n_val,
                "telefono": t_val
            }
            supabase.table("suscriptores_inmuebles").upsert(data_up, on_conflict="cedula_rif").execute()
            registrar_auditoria_db(st.session_state.user_cedula, rol_actual, "EDITAR_SUSCRIPTOR", f"Actualizó/Creó a: {s_val}")
            st.success("✅ ¡Cambios guardados en Supabase y registrados en auditoría!")
            st.rerun()
