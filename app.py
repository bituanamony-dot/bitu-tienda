import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BITU - Tienda", layout="wide")

# CONECTAR A GOOGLE SHEETS CON TUS SECRETS
@st.cache_resource
def conectar():
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet_id = st.secrets["SHEET_ID"]
    return client.open_by_key(sheet_id).sheet1

17 try:
18     sheet = conectar()
19     datos = sheet.get_all_records(expected_headers=[], head=1)
20     df = pd.DataFrame(datos)
21     df = df[df['PRODUCTO'].astype(str).str.strip() != ""]
22 except Exception as e:
23     st.error...
24     st.stop()
25
26 st.title(f"Inventario BITU ({len(df)} productos)")

st.title(f"Inventario BITU ({len(df)} productos)")

# CORREGIR EL -3: Si INV FINAL está mal, lo recalculamos
# Busca columnas, si no existen usa STOCK_ACTUAL
col_producto = 'PRODUCTO' if 'PRODUCTO' in df.columns else df.columns[0]

# Mostrar tabla
st.dataframe(df, width='stretch')

st.divider()
st.subheader("Registrar movimiento")

producto_sel = st.selectbox("Elige producto", df[col_producto].tolist())

# Encontrar fila del producto
idx_fila = df.index[df[col_producto]==producto_sel][0]
fila_sheet = idx_fila + 2 # +2 por encabezado y 1-indexed

# Detectar columnas
def get_col(nombre):
    try:
        return df.columns.get_loc(nombre) + 1
    except:
        return None

c_ent = get_col('ENTRADA')
c_ven = get_col('VENTA CALCULADA')
c_ini = get_col('INV INICIAL')
c_fin = get_col('INV FINAL')

col1, col2 = st.columns(2)

with col1:
    cant_ent = st.number_input("📦 ENTRADA", min_value=0, value=0)
    if st.button("Sumar Entrada", type="primary"):
        if c_ent:
            actual = int(str(sheet.cell(fila_sheet, c_ent).value or 0).strip() or 0)
            sheet.update_cell(fila_sheet, c_ent, actual + cant_ent)
            # Recalcular INV FINAL = INV INICIAL + ENTRADA - VENTA
            if c_ini and c_fin and c_ven:
                ini = int(str(sheet.cell(fila_sheet, c_ini).value or 0) or 0)
                ven = int(str(sheet.cell(fila_sheet, c_ven).value or 0) or 0)
                ent_nueva = actual + cant_ent
                sheet.update_cell(fila_sheet, c_fin, ini + ent_nueva - ven)
            st.success(f"Entrada de {cant_ent} guardada en {producto_sel}")
            st.cache_data.clear()
            st.rerun()

with col2:
    cant_ven = st.number_input("🛒 VENTA", min_value=0, value=0)
    if st.button("Registrar Venta"):
        if c_ven:
            actual = int(str(sheet.cell(fila_sheet, c_ven).value or 0).strip() or 0)
            sheet.update_cell(fila_sheet, c_ven, actual + cant_ven)
            if c_ini and c_fin and c_ent:
                ini = int(str(sheet.cell(fila_sheet, c_ini).value or 0) or 0)
                ent = int(str(sheet.cell(fila_sheet, c_ent).value or 0) or 0)
                sheet.update_cell(fila_sheet, c_fin, ini + ent - (actual + cant_ven))
            st.success(f"Venta de {cant_ven} guardada")
            st.cache_data.clear()
            st.rerun()

st.subheader("Últimas ventas")
st.dataframe(df.tail(10), width='stretch')
