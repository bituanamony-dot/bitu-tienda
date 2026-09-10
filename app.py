import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BITU - Tienda", layout="wide", page_icon="🛒")

@st.cache_resource
def conectar():
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    sheet_id = st.secrets["SHEET_ID"]
    sh = client.open_by_key(sheet_id)
    return sh.sheet1

def cargar_datos():
    sheet = conectar()
    datos = sheet.get_all_records()
    df = pd.DataFrame(datos)
    df = df[df['PRODUCTO'].astype(str).str.strip()!= ""]
    for c in df.columns:
        if c!= 'PRODUCTO':
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df, sheet

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

df, sheet = cargar_datos()

st.title("🛒 BITU - Tienda")
c1, c2 = st.columns([2.5, 1])

with c1:
    busca = st.text_input("🔍 Buscar", placeholder="Ej. ACEITE, AGUA, DESPENSA...")
    df_show = df[df['PRODUCTO'].str.contains(busca, case=False, na=False)] if busca else df
    st.caption(f"Productos: {len(df_show)} / {len(df)} - DESPENSA incluida")

    for i, row in df_show.iterrows():
        with st.container(border=True):
            colA, colB, colC, colD = st.columns([3,1,1,1])
            colA.markdown(f"**{row['PRODUCTO']}**")
            stock_real = int(row['INV INICIAL'] + row['ENTRADA'] - row['VENTA CALCULADA'])
            colA.caption(f"Stock: {stock_real} | Ganas: ${row['COMISION PUNTO ENTREGA']}")
            colB.metric("Precio", f"${int(row['CUOTA BANCO'])}")
           stock_real = int(row['INV INICIAL'] + row['ENTRADA'] - row['VENTA CALCULADA'])
            cant = colC.number_input("cant", 1, stock_real if stock_real>0 else 1, 1, key=f"q{i}", label_visibility="collapsed")
            if colD.button("Agregar", key=f"a{i}"):
                st.session_state.carrito.append({"producto": row['PRODUCTO'], "precio": row['CUOTA BANCO'], "comision": row['COMISION PUNTO ENTREGA'], "cant": cant, "fila": i+2})
                st.toast(f"Agregado {row['PRODUCTO']}")

with c2:
    st.subheader("Tu Venta")
    if not st.session_state.carrito:
        st.info("Carrito vacío")
    else:
        total = sum(x['precio']*x['cant'] for x in st.session_state.carrito)
        ganancia = sum(x['comision']*x['cant'] for x in st.session_state.carrito)
        for x in st.session_state.carrito:
            st.write(f"{x['cant']} x {x['producto']}")

        st.divider()
        st.metric("TOTAL", f"${int(total)}")
        st.metric("TU GANANCIA", f"${int(ganancia)}")

        if st.button("✅ COBRAR Y DESCONTAR STOCK", type="primary", use_container_width=True):
            with st.spinner("Actualizando Sheet..."):
                for item in st.session_state.carrito:
                    # Columna F = INV FINAL (6), G = VENTA CALCULADA (7) - ajusta si tu orden es diferente
                    sheet.update_cell(item['fila'], 6, int(df.iloc[item['fila']-2]['INV FINAL'] - item['cant']))
                    sheet.update_cell(item['fila'], 7, int(df.iloc[item['fila']-2]['VENTA CALCULADA'] + item['cant']))
            st.balloons()
            st.success(f"¡Cobrado! Ganaste ${int(ganancia)}")
            st.session_state.carrito = []
            st.cache_data.clear()
            st.rerun()

        if st.button("Vaciar", use_container_width=True):
            st.session_state.carrito = []
            st.rerun()
