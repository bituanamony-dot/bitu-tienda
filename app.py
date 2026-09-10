import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BITU", layout="centered")
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
        inv=int(float(row[3] or 0)); ent=int(float(row[4] or 0)); sal=int(float(row[5] or 0))
        productos.append({"fila":i+2,"nombre":row[0],"precio":float(row[1] or 0),"stock":inv+ent-sal,"inv":inv,"ent":ent,"sal":sal})
    except: continue

st.title("BITU - Tienda")

if st.session_state.carrito:
    st.info("🛒 CARRITO")
    total=0
    for nom,it in list(st.session_state.carrito.items()):
        st.write(f"{nom} x{it['cantidad']} = ${it['cantidad']*it['datos']['precio']}")
        total+=it['cantidad']*it['datos']['precio']
    st.write(f"**TOTAL ${total}**")
    if st.button("COBRAR TODO 💰", type="primary", use_container_width=True):
        for nom,it in st.session_state.carrito.items():
            p=it['datos']; ns=p['sal']+it['cantidad']
            sheet.update_cell(p['fila'],6,ns)
            sheet.update_cell(p['fila'],7,p['inv']+p['ent']-ns)
            sheet.update_cell(p['fila'],8,ns)
        st.session_state.carrito={}
        st.balloons()
        st.success("Guardado en F=SALIDA=3")
        st.rerun()
    st.divider()

for p in productos:
    st.write(f"**{p['nombre']}** - ${p['precio']} - Stock:{p['stock']}")
    if p['stock'] <=0:
        st.error("SIN STOCK")
    else:
        if st.button(f"Agregar {p['nombre']}", key=f"a{p['fila']}", use_container_width=True):
            if p['nombre'] in st.session_state.carrito:
                if st.session_state.carrito[p['nombre']]['cantidad'] < p['stock']:
                    st.session_state.carrito[p['nombre']]['cantidad']+=1
            else:
                st.session_state.carrito[p['nombre']]={"cantidad":1,"datos":p}
            st.rerun()
