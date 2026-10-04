import streamlit as st
import pandas as pd
from datetime import datetime
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from db_supabase import registrar_factura, get_tarifas, get_suscriptores

st.set_page_config(page_title="Eco Guaicaipuro - Declaración", page_icon="♻️", layout="wide")

LOGO_ECO = "Eco_Guaicaipuro.png"
LOGO_GUAICAIPURO = "Guaicaipuro_Ciudad_Capital.png"

d_suscriptor = st.session_state.get("datos_declaracion", {
    "suscriptor": "No especificado",
    "cedula": "",
    "mercado": "",
    "local": "",
    "actividad": ""
})

tasa_dolar_val = st.session_state.get("tasa_mmv_val", 0.0)

st.markdown("""
    <style>
    .main { background-color: #f4f9f4; }
    .header-box {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%);
        padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-content { flex-grow: 1; }
    .header-icon { font-size: 45px; margin-left: 20px; text-align: right; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🏛️ Identidad Institucional")
    if os.path.exists(LOGO_ECO): st.image(LOGO_ECO)
    if os.path.exists(LOGO_GUAICAIPURO): st.image(LOGO_GUAICAIPURO)
    st.markdown("---")
    fecha_actual = st.date_input("Fecha de Gestión", datetime.now())

st.markdown("""
    <div class="header-box">
        <div class="header-content">
            <h1 style="margin:0; font-size: 24px;">♻️ ECO GUAICAIPURO - Declaración y Pago Cloud</h1>
            <p style="margin:5px 0 0 0; font-size: 13px; opacity: 0.9;">Módulo de Facturación en Línea</p>
        </div>
        <div class="header-icon">📑💳</div>
    </div>
""", unsafe_allow_html=True)

if st.button("⬅️ Volver al Módulo de Gestión", use_container_width=True):
    st.switch_page("app.py")

st.markdown("---")
st.markdown("### 📑 Datos del Suscriptor Seleccionado")

st.info(f"""
* **Suscriptor:** {d_suscriptor.get('suscriptor')}
* **Cédula / RIF:** {d_suscriptor.get('cedula')}
* **Mercado:** {d_suscriptor.get('mercado')}
* **Local:** {d_suscriptor.get('local')}
* **Actividad Económica:** {d_suscriptor.get('actividad')}
""")

if st.button("💰 Pagar Aseo Urbano", use_container_width=True, type="primary"):
    st.session_state.mostrar_pago = True

if st.session_state.get("mostrar_pago", False):
    st.markdown("---")
    st.markdown("#### 🧮 Cálculo de Tarifa y Períodos")
    
    # Cargar tarifas de Supabase
    tarifas_db = get_tarifas()
    tarifa_sugerida = 3.0
    if tarifas_db:
        # Buscar coincidencia con la actividad económica
        act_actual = str(d_suscriptor.get('actividad', '')).upper()
        for t in tarifas_db:
            if t.get('tipo', '').upper() in act_actual or act_actual in t.get('descripcion', '').upper():
                tarifa_sugerida = float(t.get('tasa', 3.0))
                break

    lista_meses_opciones = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    
    mes_actual_idx = min(fecha_actual.month - 1, len(lista_meses_opciones) - 1)
    meses_seleccionados = st.multiselect(
        "Seleccione los Meses / Períodos a Pagar:",
        lista_meses_opciones,
        default=[lista_meses_opciones[mes_actual_idx]]
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tasa_cobrar = st.number_input("Tasa a Cobrar por Mes ($)", min_value=0.0, value=tarifa_sugerida, step=0.5, format="%.2f")
    with col_t2:
        dolar_bcv = st.number_input("Valor del Dólar BCV", min_value=0.0, value=float(tasa_dolar_val), disabled=True, format="%.2f")

    cantidad_meses = len(meses_seleccionados) if meses_seleccionados else 1
    total_pagar = tasa_cobrar * dolar_bcv * cantidad_meses
    
    def fmt_monto(val):
        try:
            num = float(val)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return str(val)

    total_pagar_fmt = fmt_monto(total_pagar)

    st.markdown(f"##### Cantidad de meses seleccionados: **{cantidad_meses}**")
    if st.button(f"📌 Total a Pagar ({cantidad_meses} Meses): Bs. {total_pagar_fmt}", use_container_width=True, type="secondary"):
        st.session_state.monto_auto = f"{total_pagar:.2f}"
        st.rerun()

    st.markdown("---")
    st.markdown("#### 💳 Datos del Pago")

    bancos_lista = [
        "0102: Banco de Venezuela", "0134: Banesco", "0105: Banco Mercantil", 
        "0108: BBVA Provincial", "0191: Banco Nacional de Crédito", "0172: Bancamiga", 
        "0114: Bancaribe", "0163: Banco del Tesoro", "0175: Banco Digital de los Trabajadores", 
        "0157: Delsur", "0115: Banco Exterior", "0156: 100% Banco", 
        "0177: BanFANB", "0138: Banco Plaza", "0171: Banco Activo"
    ]
    bancos_destino = ["0172: Bancamiga", "0175: Banco Digital de los Trabajadores"]

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        banco_origen = st.selectbox("Banco del cual se pagó:", bancos_lista)
    with col_b2:
        banco_destino = st.selectbox("Banco al cual se realizó el pago:", bancos_destino)

    col_b3, col_b4 = st.columns(2)
    with col_b3:
        num_ref = st.text_input("Número de Referencia del Pago")
    with col_b4:
        monto_sugerido = st.session_state.get("monto_auto", "")
        monto_pagado = st.text_input("Monto Pagado (Bs.)", value=monto_sugerido)

    st.markdown("")
    if st.button("🚀 Ejecutar Pago", use_container_width=True):
        st.success("¡Pago ejecutado con éxito en la nube!")
        st.session_state.pago_ejecutado = True

    if st.session_state.get("pago_ejecutado", False):
        st.markdown("---")
        if st.button("📄 Generar Planilla de Pago en PDF y Registrar en Supabase", use_container_width=True, type="secondary"):
            hoy_str = fecha_actual.strftime("%d%m%Y")
            
            from db_supabase import supabase
            res_count = supabase.table("facturacion_historial").select("id", count="exact").execute()
            consecutivo_num = f"{(res_count.count or 0) + 1:03d}"

            mercado_nombre = d_suscriptor.get('mercado', '').upper()
            if "PLAZA" in mercado_nombre:
                siglas_mercado = "MERPL"
            elif "VENCEDORES" in mercado_nombre:
                siglas_mercado = "MERVE"
            elif "PASO" in mercado_nombre:
                siglas_mercado = "MERPA"
            else:
                siglas_mercado = "LOCDE"

            local_str = str(d_suscriptor.get('local', '00')).replace(" ", "").upper()
            codigo_planilla = f"Eco-{siglas_mercado}-{hoy_str}-{local_str}-{consecutivo_num}".upper()

            carpeta_fecha = hoy_str
            os.makedirs(carpeta_fecha, exist_ok=True)
            nombre_pdf = f"Planilla_{codigo_planilla.replace('-', '_')}.pdf"
            ruta_pdf = os.path.join(carpeta_fecha, nombre_pdf)

            s_comercial = d_suscriptor.get('suscriptor', '').upper()
            s_mercado = d_suscriptor.get('mercado', '').upper()
            meses_a_imprimir = meses_seleccionados if meses_seleccionados else [f"MES/{fecha_actual.year}"]
            periodo_str_guardar = ", ".join(meses_a_imprimir)

            # Registrar en Supabase (facturacion_historial)
            registro_db = {
                "no": consecutivo_num,
                "fecha": fecha_actual.strftime("%d-%m-%Y"),
                "codigo_planilla": codigo_planilla,
                "nombre_comercial": s_comercial,
                "periodo_pagado": periodo_str_guardar,
                "total_pagado": f"BS. {fmt_monto(total_pagar)}",
                "direccion": s_mercado
            }
            registrar_factura(registro_db)

            # Generar PDF con ReportLab
            doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=100)
            story = []
            styles = getSampleStyleSheet()

            COLOR_AZUL = colors.HexColor('#3b5998')
            COLOR_AMARILLO = colors.HexColor('#ffeb3b')
            COLOR_GRIS_CLARO = colors.HexColor('#f8f9fa')

            style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=9, alignment=1, textColor=colors.HexColor('#000000'), fontName='Helvetica-Bold')
            style_normal = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#000000'), fontName='Helvetica')
            style_bold = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#000000'), fontName='Helvetica-Bold')
            style_center_bold = ParagraphStyle('CenterBold', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.HexColor('#000000'), fontName='Helvetica-Bold')

            alicuota_fmt = fmt_monto(tasa_cobrar)
            monto_pagado_fmt = fmt_monto(monto_pagado) if monto_pagado else "0,00"

            def dibujar_elementos_pagina(canvas_obj, doc_obj):
                canvas_obj.saveState()
                if os.path.exists(LOGO_ECO):
                    canvas_obj.setFillAlpha(0.08)
                    canvas_obj.drawImage(LOGO_ECO, (612-480)/2, (792-480)/2, width=480, height=480, mask='auto')
                canvas_obj.restoreState()
                canvas_obj.saveState()
                centro_x = 612 / 2
                y_base = 42
                canvas_obj.setLineWidth(0.75)
                canvas_obj.line(centro_x - 120, y_base + 32, centro_x + 120, y_base + 32)
                canvas_obj.setFont("Helvetica-Bold", 8)
                canvas_obj.drawCentredString(centro_x, y_base + 20, "LIC. HUGO ROMERO")
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.drawCentredString(centro_x, y_base + 10, "PRESIDENTE DE ECO GUAICAIPURO, S.A.")
                canvas_obj.setFont("Helvetica", 7)
                canvas_obj.setFillColor(colors.HexColor('#666666'))
                canvas_obj.drawCentredString(centro_x, y_base, "RES. Nº DAMBG-001-2026 DE FECHA 07/01/2026")
                canvas_obj.restoreState()

            logo_izq = Image(LOGO_ECO, width=130, height=130) if os.path.exists(LOGO_ECO) else Paragraph("", style_normal)
            logo_der = Image(LOGO_GUAICAIPURO, width=130, height=130) if os.path.exists(LOGO_GUAICAIPURO) else Paragraph("", style_normal)
            
            texto_encabezado = [
                Spacer(1, 10),
                Paragraph("<b>REPÚBLICA BOLIVARIANA DE VENEZUELA</b>", style_center_bold),
                Paragraph("<b>ESTADO MIRANDA</b>", style_center_bold),
                Paragraph("<b>ECOGUAICAIPURO</b>", style_center_bold),
                Paragraph("<b>G-200176636</b>", style_center_bold)
            ]
            story.append(Table([[logo_izq, texto_encabezado, logo_der]], colWidths=[110, 330, 110]))
            story.append(Spacer(1, 6))

            story.append(Table([[Paragraph("<b>PLANILLA DE PAGO CLOUD</b>", ParagraphStyle('T', parent=style_title, alignment=1, textColor=colors.whitesmoke, fontSize=11))]], colWidths=[550], style=[('BACKGROUND', (0,0), (-1,-1), COLOR_AZUL), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            story.append(Spacer(1, 5))

            s_cedula = d_suscriptor.get('cedula', '').upper()
            s_pasillo = str(d_suscriptor.get('pasillo', '')).upper()
            s_local = str(d_suscriptor.get('local', '')).upper()

            info_cliente = [
                [Paragraph(f"<b>NOMBRE COMERCIAL:</b> {s_comercial}", style_normal), Paragraph("<b>ESTADO:</b> PAGADO", style_normal)],
                [Paragraph(f"<b>IDENTIFICACIÓN:</b> {s_cedula}", style_normal), Paragraph("<b>ESTATUS:</b> VALIDADO CLOUD", style_normal)],
                [Paragraph(f"<b>DIRECCIÓN:</b> {s_mercado}", style_normal), Paragraph(f"<b>LOCAL:</b> {s_local}", style_normal)]
            ]
            story.append(Table(info_cliente, colWidths=[350, 200], style=[('BACKGROUND', (0,0), (-1,-1), COLOR_GRIS_CLARO), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d0d0d0'))]))
            story.append(Spacer(1, 6))

            doc.build(story, onFirstPage=dibujar_elementos_pagina, onLaterPages=dibujar_elementos_pagina)

            st.balloons()
            st.success(f"✅ ¡Planilla registrada en Supabase y PDF generado con éxito en `{ruta_pdf}`!")
            
            with open(ruta_pdf, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Descargar Planilla en PDF",
                data=pdf_bytes,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True
            )
