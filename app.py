import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="BITU", layout="wide")
scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["SHEET_ID"]).sheet1

if "carrito" not in st.session_state:
    st.session_state.carrito = {}

data = sheet.get_all_values()
productos=[]
for i,row in enumerate(data[1:]):
    if not row[0]: continue
    try:
        inv_ini=int(float(row[3] or 0)); entrada=int(float(row[4] or 0)); salida=int(float(row[5] or 0))
        stock = inv_ini + entrada - salida
        productos.append({"fila":i+2,"nombre":row[0],"precio":float(row[1] or 0),"stock":stock,"inv_ini":inv_ini,"entrada":entrada,"salida":salida})
    except: continue

st.title("BITU - Tienda")

# CARRITO ARRIBA PARA QUE LO VEAS
if st.session_state.carrito:
    st.success(f"Carrito: {len(st.session_state.carrito)} productos")
    total=0
    for nom, it in list(st.session_state.carrito.items()):
        c1,c2,c3 = st.columns([2,1,1])
        c1.write(f"{nom} x{it['cantidad']}")
        total+= it['cantidad']*it['datos']['precio']
        if c3.button("Quitar", key=f"q_{nom}"):
            del st.session_state.carrito[nom]
            st.rerun()
    st.write(f"### Total: ${total}")
    if st.button("COBRAR TODO 💰", type="primary"):
        for nom, it in st.session_state.carrito.items():
            p=it['datos']; ns=p['salida']+it['cantidad']
            sheet.update_cell(p['fila'], 6, ns) # F = SALIDA = 3
            sheet.update_cell(p['fila'], 7, p['inv_ini']+p['entrada']-ns)
            sheet.update_cell(p['fila'], 8, ns)
        st.session_state.carrito={}
        st.balloons()
        st.success("Venta guardada en F=SALIDA!")
        st.rerun()

st.divider()

for p in productos:
    c1,c2,c3 = st.columns([2,1,1])
    c1.write(f"**{p['nombre']}** - ${p['precio']} - Stock:{p['stock']}")
    if p['stock'] <= 0:
        c3.error("SIN STOCK")
    else:
        if c3.button("Agregar +", key=f"add_{p['fila']}"):
            if p['nombre'] in st.session_state.carrito:
                if st.session_state.carrito[p['nombre']]['cantidad'] < p['stock']:
                    st.session_state.carrito[p['nombre']]['cantidad'] += 1
            else:
                st.session_state.carrito[p['nombre']] = {"cantidad":1, "datos":p}
            st.rerun()
