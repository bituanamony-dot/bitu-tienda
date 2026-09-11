import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="BITU", page_icon="🛒", layout="centered")

# --- LOGO ---
col_logo, col_title = st.columns([1,3])
with col_logo:
    st.image("logo.png", width=100)
with col_title:
    st.title("BITU")
    st.caption("Tienda - Pachuca, Hgo.")

scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["SHEET_ID"]).sheet1

if "carrito" not in st.session_state:
    st.session_state.carrito = {}

data = sheet.get_all_values()
productos=[]
total_vendido_general = 0
total_cobrado_general = 0

for i,row in enumerate(data[1:]):
    if not row[0]: continue
    try:
        inv=int(float(row[3] or 0)); ent=int(float(row[4] or 0)); sal=int(float(row[5] or 0))
        precio=float(row[1] or 0)
        productos.append({"fila":i+2,"nombre":row[0],"precio":precio,"stock":inv+ent-sal,"inv":inv,"ent":ent,"sal":sal})
        total_vendido_general += sal
        total_cobrado_general += sal * precio
    except: continue

tab1, tab2 = st.tabs(["🛒 TIENDA", "📊 REPORTE GENERAL"])

with tab1:
    if st.session_state.carrito:
        with st.container(border=True):
            st.subheader(f"🛒 Carrito ({len(st.session_state.carrito)})")
            total=0
            for nom,it in list(st.session_state.carrito.items()):
                c1,c2,c3 = st.columns([3,1,1])
                c1.write(f"**{nom}** x{it['cantidad']}")
                total+=it['cantidad']*it['datos']['precio']
                c2.write(f"${it['cantidad']*it['datos']['precio']:.0f}")
                if c3.button("❌", key=f"q_{nom}"):
                    del st.session_state.carrito[nom]
                    st.rerun()
            st.metric("TOTAL A COBRAR", f"${total:.0f}")
            if st.button("✅ COBRAR TODO", type="primary", use_container_width=True):
                for nom,it in st.session_state.carrito.items():
                    p=it['datos']; ns=p['sal']+it['cantidad']
                    sheet.update_cell(p['fila'], 6, ns)
                    sheet.update_cell(p['fila'], 7, p['inv']+p['ent']-ns)
                    sheet.update_cell(p['fila'], 8, ns)
                st.session_state.carrito={}
                st.balloons()
                st.success("Venta guardada en F=SALIDA=3")
                st.rerun()
    else:
        st.info("Agrega productos para vender")

    for p in productos:
        with st.container(border=True):
            c1,c2 = st.columns([3,1])
            c1.markdown(f"**{p['nombre']}** | ${p['precio']:.0f} | Stock: {p['stock']}")
            if p['stock']<=0:
                c2.error("Agotado")
            else:
                if c2.button("Agregar +", key=f"a{p['fila']}", use_container_width=True):
                    if p['nombre'] in st.session_state.carrito:
                        if st.session_state.carrito[p['nombre']]['cantidad'] < p['stock']:
                            st.session_state.carrito[p['nombre']]['cantidad']+=1
                    else:
                        st.session_state.carrito[p['nombre']]={"cantidad":1,"datos":p}
                    st.rerun()

with tab2:
    st.subheader("📊 Reporte General")
    st.caption("Esta es la hoja que importas - Resumen total cobrado")
    c1,c2 = st.columns(2)
    c1.metric("TOTAL ARTÍCULOS VENDIDOS", f"{total_vendido_general} pzas")
    c2.metric("TOTAL COBRADO", f"${total_cobrado_general:,.0f}")
    st.divider()
    for p in productos:
        st.write(f"{p['nombre']}: Vendidos {p['sal']} = ${p['sal']*p['precio']:.0f}")
