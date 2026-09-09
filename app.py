import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BITU - Tienda", layout="wide")

# CONECTAR A GOOGLE SHEETS CON TUS SECRETS
@st.cache_resource
def conectar():
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    sheet_id = st.secrets["SHEET_ID"]
    return client.open_by_key(sheet_id).sheet1

try:
    sheet = conectar()
    datos = sheet.get_all_records(expected_headers=[], head=1)
    df = pd.DataFrame(datos)
    df = df[df['PRODUCTO'].astype(str).str.strip()!= ""]
except Exception as e:
    st.error(f"No pude conectar a Sheets: {e}")
    st.info("Verifica Secrets y que compartiste la Sheet con bitu-app@cosmic-tensor-508103-f1.iam.gserviceaccount.com")
    st.stop()

st.title(f"Inventario BITU ({len(df)} productos)")

# CORREGIR EL -3: Si INV FINAL está mal, lo recalculamos
# Busca columnas, si no existen usa STOCK_ACTUAL
col_producto = 'PRODUCTO' if 'PRODUCTO' in df.columns else df.columns[0]

# Mostrar tabla
st.dataframe(df, use_container_width=True)

