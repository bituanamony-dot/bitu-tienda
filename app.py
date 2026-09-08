import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="BITU - Banco de Insumos", page_icon="logo.png", layout="wide")

col_logo, col_tit = st.columns([1,4])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
with col_tit:
    st.title("BITU")
    st.write("**Banco de Insumos Todos Unidos**")
    st.caption('"CUANDO NOS UNIMOS, ALCANZA PARA TODOS" - ASOCIACION CIVIL SIN FINES DE LUCRO')

ARCHIVO_PRODUCTOS = "productos.xlsx"
ARCHIVO_VENTAS = "ventas.xlsx"

@st.cache_data
def cargar_productos():
    return pd.read_excel(ARCHIVO_PRODUCTOS)

try:
    df_productos = cargar_productos()
except:
    st.error("Cierra tu Excel y recarga con R")
    st.stop()

if os.path.exists(ARCHIVO_VENTAS):
    df_ventas = pd.read_excel(ARCHIVO_VENTAS)
else:
    df_ventas = pd.DataFrame(columns=["FECHA","PRODUCTO","CANTIDAD","PRECIO","GANANCIA"])

stock_vendido = df_ventas.groupby("PRODUCTO")["CANTIDAD"].sum().to_dict()
df_productos["VENDIDO"] = df_productos["PRODUCTO"].map(stock_vendido).fillna(0)
if "INICIAL" in df_productos.columns:
    df_productos["INICIAL"] = pd.to_numeric(df_productos["INICIAL"], errors='coerce').fillna(0)
    df_productos["STOCK_ACTUAL"] = df_productos["INICIAL"] - df_productos["VENDIDO"]
else:
    df_productos["STOCK_ACTUAL"] = 999

c1, c2 = st.columns([1,2])
with c1:
    st.subheader("Registrar Venta BITU")
    producto = st.selectbox("Producto:", df_productos["PRODUCTO"].tolist())
    datos = df_productos[df_productos["PRODUCTO"]==producto].iloc[0]
    st.metric("Precio", f"${datos['PRECIO']}", f"Stock: {int(datos['STOCK_ACTUAL'])}")
    cantidad = st.number_input("Cantidad:", min_value=1, max_value=int(datos['STOCK_ACTUAL']) if datos['STOCK_ACTUAL']>0 else 1, value=1)
    if st.button("✅ VENDER", type="primary", use_container_width=True):
        nueva_venta = {
            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "PRODUCTO": producto,
            "CANTIDAD": cantidad,
            "PRECIO": datos['PRECIO']*cantidad,
            "GANANCIA": 0
        }
        df_ventas = pd.concat([df_ventas, pd.DataFrame([nueva_venta])], ignore_index=True)
        df_ventas.to_excel(ARCHIVO_VENTAS, index=False)
        st.success(f"Vendido {cantidad} x {producto}")
        st.cache_data.clear()
        st.rerun()
    if not df_ventas.empty:
        hoy = datetime.now().strftime("%Y-%m-%d")
        ventas_hoy = df_ventas[df_ventas["FECHA"].astype(str).str.contains(hoy)]
        st.metric("Ventas hoy BITU", f"${ventas_hoy['PRECIO'].sum():.0f}")

with c2:
    st.subheader(f"Inventario BITU ({len(df_productos)} productos)")
    st.dataframe(df_productos[["PRODUCTO","STOCK_ACTUAL","PRECIO","VENDIDO"]].sort_values("STOCK_ACTUAL"), use_container_width=True, height=400)
    st.subheader("Últimas ventas")
    if not df_ventas.empty:
        st.dataframe(df_ventas.tail(10).sort_values("FECHA", ascending=False), use_container_width=True)