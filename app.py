import streamlit as st
import gspread
from google.oauth2client.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="BITU", page_icon="🛒", layout="wide")

# --- CONEXION A GOOGLE SHEET ---
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(st.secrets["sheet_url"]).sheet1

# --- LEER DATOS ---
data = sheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# Columnas segun tu foto
# B=CUOTA BANCO(1), C=COMISION(2), D=INV INICIAL(3), E=ENTRADA(4), F=SALIDA(5), G=INV FINAL(6), H=VENTA CALC(7), I=CUOTA VENTA(8)
# En python es indice 0, asi que F=5, G=6, H=7

productos = []
for i, row in df.iterrows():
    try:
        inv_inicial = int(float(row[3] or 0)) # D
        entrada = int(float(row[4] or 0)) # E
        salida = int(float(row[5] or 0)) # F
        stock = inv_inicial + entrada - salida
        if stock < 0: stock = 0

        productos.append({
            "fila": i+2,
            "nombre": row[0],
            "precio": float(row[1] or 0),
            "comision": float(row[2] or 0),
            "inv_inicial": inv_inicial,
            "entrada": entrada,
            "salida": salida,
            "stock": stock,
            "index": i
        })
    except:
        continue

# --- INTERFAZ ---
st.markdown("<h1 style='color:#0E9F9F'>BITU - Punto de Venta</h1>", unsafe_allow_html=True)

if "carrito" not in st.session_state:
    st.session_state.carrito = {}

col1, col2 = st.columns([2,1])

with col1:
    for p in productos:
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            st.write(f"**{p['nombre']}** - ${p['precio']} - Stock: {p['stock']}")
        with c2:
            if p['stock'] <= 0:
                st.error("⛔ SIN STOCK")
            else:
                if st.button("Agregar", key=f"add_{p['index']}"):
                    if p['nombre'] in st.session_state.carrito:
                        if st.session_state.carrito[p['nombre']]['cantidad'] < p['stock']:
                            st.session_state.carrito[p['nombre']]['cantidad'] += 1
                        else:
                            st.warning("No hay mas stock")
                    else:
                        st.session_state.carrito[p['nombre']] = {"cantidad": 1, "datos": p}

with col2:
    st.subheader("Carrito")
    total = 0
    comision_total = 0
    for nombre, item in st.session_state.carrito.items():
        cant = item['cantidad']
        precio = item['datos']['precio']
        com = item['datos']['comision']
        st.write(f"{nombre} x{cant} = ${cant*precio}")
        total += cant*precio
        comision_total += cant*com

    st.write(f"**Total: ${total}**")
    st.write(f"Tu comisión: ${comision_total}")

    if st.button("COBRAR 💰"):
        for nombre, item in st.session_state.carrito.items():
            p = item['datos']
            fila = p['fila']
            nueva_salida = p['salida'] + item['cantidad']
            nuevo_inv_final = p['inv_inicial'] + p['entrada'] - nueva_salida

            # ACTUALIZACION CORRECTA
            sheet.update_cell(fila, 6, nueva_salida) # F = SALIDA <- AQUI CAE LA VENTA
            sheet.update_cell(fila, 7, nuevo_inv_final) # G = INV FINAL = D+E-F
            sheet.update_cell(fila, 8, nueva_salida) # H = VENTA CALCULADA = F
            sheet.update_cell(fila, 9, float(sheet.cell(fila, 2).value or 0) * nueva_salida) # I = CUOTA VENTA

        st.success("Venta guardada en SALIDA (F)")
        st.session_state.carrito = {}
        st.rerun()
