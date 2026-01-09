import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema USAG - Online", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Esto reemplaza al sistema de CSV anterior
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_historial():
    # ttl=0 significa que no guarde caché, que lea siempre lo nuevo
    try:
        df = conn.read(worksheet="Hoja 1", ttl=0)
        return df
    except:
        return pd.DataFrame()

def guardar_entrenamiento(datos):
    try:
        # 1. Leemos lo que ya existe
        df_existente = cargar_historial()
        
        # 2. Convertimos el nuevo dato en DataFrame
        df_nuevo = pd.DataFrame([datos])
        
        # 3. Pegamos lo nuevo al final de lo viejo
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        
        # 4. Subimos todo a Google Sheets
        conn.update(worksheet="Hoja 1", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
        return False

# --- USUARIOS (CONFIGURA TUS ALUMNAS) ---
USUARIOS = {
    "12345678": {"nombre": "Ana Ejemplo", "nivel": "Desarrollo (Nivel 3-5)"},
    "87654321": {"nombre": "María Avanzada", "nivel": "Opcional/Elite (Nivel 6-10)"},
    "11112222": {"nombre": "Sofía Nueva", "nivel": "Desarrollo (Nivel 3-5)"},
}
PASSWORD_ADMIN = "entrenadora123"

# --- LÓGICA DE ENTRENAMIENTO (Planificación) ---
def obtener_plan(fase, nivel, dia_semana):
    fisico, tecnico, calentamiento = [], [], []
    es_avanzado = "6-10" in nivel
    
    # Calentamiento
    if fase == "Fase Competitiva":
        calentamiento = ["Cardio Suave (10')", "Flexibilidad (10')", "Básicos (10')"]
    else:
        calentamiento = ["Cardio (5')", "Movilidad (5')", "Postura (5')"]

    # Rutina simplificada para el ejemplo (AQUI VA TU LÓGICA COMPLETA)
    if dia_semana == "Monday":
        foco = "Salto y Piernas"
        fisico = ["Sentadillas", "Saltos Cajón"]
        tecnico = ["Carrera", "Entrada Flatback"]
    elif dia_semana == "Tuesday":
        foco = "Barras y Tracción"
        fisico = ["Dominadas", "Leg Lifts"]
        tecnico = ["Kips", "Cast a Vertical"]
    elif dia_semana == "Wednesday":
        foco = "Viga y Core"
        fisico = ["Hollow Rocks", "Planchas"]
        tecnico = ["Acrobacia Viga", "Danza"]
    elif dia_semana == "Thursday":
        foco = "Suelo y Empuje"
        fisico = ["Flexiones", "V-ups"]
        tecnico = ["Tumbling", "Rutinas Suelo"]
    elif dia_semana == "Friday":
        foco = "Control / Modelaje"
        fisico = ["Circuito Metabólico"]
        tecnico = ["Simulacro Competencia"]
    else:
        foco = "Descanso"
        
    return {"calentamiento": calentamiento, "fisico": fisico, "tecnico": tecnico, "foco": foco}

# --- GESTIÓN DE SESIÓN ---
if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if 'es_admin' not in st.session_state: st.session_state['es_admin'] = False
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = {}

def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso USAG Online</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Gimnastas", "Entrenadora"])
    
    with tab1:
        with st.form("login_gimnasta"):
            dni = st.text_input("Ingresa tu DNI")
            if st.form_submit_button("Entrar", use_container_width=True):
                if dni in USUARIOS:
                    st.session_state['logueado'] = True
                    st.session_state['es_admin'] = False
                    st.session_state['usuario_actual'] = USUARIOS[dni]
                    st.session_state['usuario_actual']['dni'] = dni
                    st.rerun()
                else:
                    st.error("DNI no encontrado.")
    with tab2:
        with st.form("login_admin"):
            pwd = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar Admin", use_container_width=True):
                if pwd == PASSWORD_ADMIN:
                    st.session_state['logueado'] = True
                    st.session_state['es_admin'] = True
                    st.rerun()
                else:
                    st.error("Incorrecto")

def logout():
    st.session_state['logueado'] = False
    st.session_state['es_admin'] = False
    st.rerun()

# --- VISTAS ---
def mostrar_dashboard():
    st.title("📊 Panel Entrenadora (Google Sheets)")
    
    # Cargar datos reales de la nube
    with st.spinner("Descargando datos de Google Sheets..."):
        df = cargar_historial()
    
    if df.empty:
        st.warning("La hoja está vacía o no se pudo conectar.")
    else:
        # Métricas
        col1, col2 = st.columns(2)
        col1.metric("Total Entrenamientos", len(df))
        col2.metric("Último Registro", df.iloc[-1]['Fecha'] if not df.empty else "-")
        
        st.subheader("📋 Historial en Vivo")
        st.dataframe(df)
        st.markdown(f"[Ver Hoja de Cálculo en Google]({st.secrets['connections']['gsheets']['spreadsheet']})")

def mostrar_app_gimnasta():
    user = st.session_state['usuario_actual']
    with st.sidebar:
        st.write(f"Hola, **{user['nombre']}**")
        if st.button("Salir"): logout()
        fecha = st.date_input("Fecha", datetime.now())
        fase = st.selectbox("Fase", ["Fase Base", "Fase Carga", "Fase Competitiva"])

    dia_ing = fecha.strftime("%A")
    plan = obtener_plan(fase, user['nivel'], dia_ing)
    
    if plan['foco'] == "Descanso":
        st.info("Día de descanso.")
    else:
        st.header(f"Plan: {plan['foco']}")
        completados = 0
        total = len(plan['calentamiento'] + plan['fisico'] + plan['tecnico'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Físico")
            for i in plan['calentamiento'] + plan['fisico']:
                if st.checkbox(i, key=i): completados += 1
        with col2:
            st.subheader("Técnico")
            for i in plan['tecnico']:
                if st.checkbox(i, key=i): completados += 1
        
        notas = st.text_area("Notas:")
        progreso = completados / total if total > 0 else 0
        st.progress(progreso)
        
        if st.button("✅ GUARDAR EN LA NUBE", type="primary"):
            datos = {
                "Fecha": str(fecha),
                "Hora": datetime.now().strftime("%H:%M"),
                "DNI": user['dni'],
                "Atleta": user['nombre'],
                "Nivel": user['nivel'],
                "Fase": fase,
                "Foco": plan['foco'],
                "Cumplimiento": f"{int(progreso * 100)}%",
                "Notas": notas
            }
            with st.spinner("Subiendo a Google Sheets..."):
                if guardar_entrenamiento(datos):
                    st.success("¡Guardado exitoso!")
                    st.balloons()
                    time.sleep(2)

# --- MAIN ---
if not st.session_state['logueado']:
    login()
else:
    if st.session_state['es_admin']:
        mostrar_dashboard()
    else:
        mostrar_app_gimnasta()