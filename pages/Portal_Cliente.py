import streamlit as st
import pandas as pd
from db_supabase import get_suscriptores, get_facturacion

st.set_page_config(page_title="Eco Guaicaipuro - Portal del Suscriptor", page_icon="📱", layout="wide")

st.markdown("### 📱 Portal de Autogestión del Suscriptor")

cedula_cli = st.session_state.get("cedula_cliente_portal", "")
if not cedula_cli:
    cedula_cli = st.text_input("Ingrese su Cédula o RIF:")

if cedula_cli:
    suscriptores = get_suscriptores()
    match = [s for s in suscriptores if str(s.get("cedula_rif")).strip().upper() == cedula_cli.strip().upper()]
    
    if match:
        s = match[0]
        st.success(f"¡Bienvenido, {s.get('suscriptor')}!")
        st.info(f"**Dirección:** {s.get('direccion')} | **Código:** {s.get('codigo')} | **Actividad:** {s.get('actividad_economica')}")
        
        st.markdown("#### 📑 Historial de Pagos y Estado de Cuenta")
        facturas = get_facturacion()
        mis_facturas = [f for f in facturas if str(f.get("nombre_comercial")).strip().upper() == str(s.get("suscriptor")).strip().upper()]
        
        if mis_facturas:
            st.dataframe(pd.DataFrame(mis_facturas), use_container_width=True)
        else:
            st.warning("No tiene pagos registrados en el sistema todavía.")
    else:
        st.error("❌ Cédula o RIF no encontrado en la base de datos.")

if st.button("⬅️ Volver al Inicio"):
    st.switch_page("app.py")
