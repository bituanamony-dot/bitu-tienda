import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="BITU")
scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheet_ID"]).sheet1

data = sheet.get_all_values()
productos=[]
for i,row in enumerate(data[1:]):
    try:
        inv_ini=int(float(row[3] or 0)); entrada=int(float(row[4] or 0)); salida=int(float(row[5] or 0))
        productos.append({"fila":i+2,"nombre":row[0],"precio":float(row[1] or 0),"comision":float(row[2] or 0),"inv_ini":inv_ini,"entrada":entrada,"salida":salida,"stock":inv_ini+entrada-salida})
    except: continue

if "carrito" not in st.session_state: st.session_state.carrito={}
st.title("BITU - Tienda")
for p in productos:
    c1,c2=st.columns([3,1])
    c1.write(f"{p['nombre']} Stock:{p['stock']}")
    if p['stock']>0 and c2.button("Agregar",key=f"a{p['fila']}"):
        if p['nombre'] in st.session_state.carrito:
            if st.session_state.carrito[p['nombre']]['cantidad'] < p['stock']: st.session_state.carrito[p['nombre']]['cantidad']+=1
        else: st.session_state.carrito[p['nombre']]={"cantidad":1,"datos":p}

st.divider()
total=0
for nom,it in st.session_state.carrito.items():
    st.write(f"{nom} x{it['cantidad']}"); total+=it['cantidad']*it['datos']['precio']
st.write(f"Total ${total}")
if st.button("COBRAR"):
    for nom,it in st.session_state.carrito.items():
        p=it['datos']; ns=p['salida']+it['cantidad']
        sheet.update_cell(p['fila'],6,ns)
        sheet.update_cell(p['fila'],7,p['inv_ini']+p['entrada']-ns)
        sheet.update_cell(p['fila'],8,ns)
    st.session_state.carrito={}; st.success("Venta guardada!"); st.rerun()
