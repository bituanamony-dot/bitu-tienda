import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from PIL import Image
import os

st.set_page_config(page_title="BITU - Tienda", layout="wide", page_icon="🛒")

# --- LOGO + ESTILO TEAL ---
st.markdown("""
<style>
.stButton>button[kind="primary"]{background-color:#009688!important; border-color:#009688!important;}
div[data-testid="stMetricValue"]{color:#009688;}
</style>
""", unsafe_allow_html=True)

col_logo, col_titulo = st.columns([1,4])
if os.path.exists("logo.png"):
    col_logo.image("logo.png", width=90)
else:
    col_logo.markdown("# 🛒")
col_titulo.title("BITU - Tienda")
col_titulo.caption("Con control de stock - Tema Teal")

# --- CONEXION ---
@st.cache_resource
def conectar():
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    return sh.sheet1

def cargar_datos():
    sheet = conectar()
    df = pd.DataFrame(sheet.get_all_records())
    df = df[df['PRODUCTO'].astype(str).str.strip()!= ""]
    for c in df.columns:
        if c!='PRODUCTO': df[c]=pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df, sheet

if 'carrito' not in st.session_state: st.session_state.carrito=[]

df, sheet = cargar_datos()

c1,c2 = st.columns([2.5,1])
with c1:
    busca = st.text_input("🔍 Buscar", placeholder="ACEITE, AGUA, DESPENSA...")
    df_show = df[df['PRODUCTO'].str.contains(busca, case=False, na=False)] if busca else df
    for i,row in df_show.iterrows():
        stock_real = int(row['INV INICIAL'] + row['ENTRADA'] - row['VENTA CALCULADA'])
        with st.container(border=True):
            colA,colB,colC,colD = st.columns([3,1,1,1])
            colA.markdown(f"**{row['PRODUCTO']}**")
            if stock_real <= 0:
                colA.markdown("<span style='color:red'>⛔ SIN STOCK</span>", unsafe_allow_html=True)
            else:
                colA.caption(f"Stock: {stock_real} | Ganas: ${int(row['COMISION PUNTO ENTREGA'])}")
            colB.metric("Precio", f"${int(row['CUOTA BANCO'])}")
            if stock_real <= 0:
                colC.number_input("c",1,1,1,key=f"q{i}",disabled=True,label_visibility="collapsed")
                colD.button("Sin stock", key=f"a{i}", disabled=True)
            else:
                cant = colC.number_input("c",1,stock_real,1,key=f"q{i}",label_visibility="collapsed")
                if colD.button("Agregar", key=f"a{i}"):
                    en_carrito = sum(x['cant'] for x in st.session_state.carrito if x['producto']==row['PRODUCTO'])
                    if en_carrito + cant > stock_real:
                        st.error(f"Solo quedan {stock_real - en_carrito}")
                    else:
                        st.session_state.carrito.append({"producto":row['PRODUCTO'],"precio":row['CUOTA BANCO'],"comision":row['COMISION PUNTO ENTREGA'],"cant":cant,"fila":i+2,"venta_actual":row['VENTA CALCULADA']})
                        st.toast(f"Agregado {row['PRODUCTO']}")

with c2:
    st.subheader("Tu Venta")
    if not st.session_state.carrito: st.info("Carrito vacío")
    else:
        total = sum(x['precio']*x['cant'] for x in st.session_state.carrito)
        gan = sum(x['comision']*x['cant'] for x in st.session_state.carrito)
        for x in st.session_state.carrito: st.write(f"{x['cant']} x {x['producto']}")
        st.divider()
        st.metric("TOTAL", f"${int(total)}")
        st.metric("TU GANANCIA", f"${int(gan)}")
        if st.button("✅ COBRAR Y DESCONTAR", type="primary", use_container_width=True):
            with st.spinner("Descontando stock..."):
                for item in st.session_state.carrito:
                    sheet.update_cell(item['fila'], 7, int(item['venta_actual'] + item['cant']))
            st.balloons(); st.success(f"¡Cobrado! Ganaste ${int(gan)}")
            st.session_state.carrito=[]; st.rerun()
        if st.button("Vaciar", use_container_width=True):
            st.session_state.carrito=[]; st.rerun()
