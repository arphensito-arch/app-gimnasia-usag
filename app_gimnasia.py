import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema USAG - Online", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Cargar Historial de Entrenamientos (Hoja "Historial")
def cargar_historial():
    try:
        # AQUÍ ESTÁ EL CAMBIO: Lee la hoja llamada "Historial"
        return conn.read(worksheet="Historial", ttl=0)
    except:
        return pd.DataFrame()

# 2. Cargar Lista de Usuarios (Hoja "Usuarios")
def cargar_usuarios_db():
    try:
        df = conn.read(worksheet="Usuarios", ttl=0)
        # Convertimos DNI a texto para no perder ceros iniciales
        df['DNI'] = df['DNI'].astype(str) 
        return df
    except Exception as e:
        st.error(f"Error leyendo usuarios: {e}")
        return pd.DataFrame(columns=["DNI", "Nombre", "Nivel"])

# 3. Guardar Entrenamiento en "Historial"
def guardar_entrenamiento(datos):
    try:
        df_existente = cargar_historial()
        df_nuevo = pd.DataFrame([datos])
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        
        # AQUÍ ESTÁ EL CAMBIO: Guarda en la hoja "Historial"
        conn.update(worksheet="Historial", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# 4. Actualizar Usuarios (Agregar/Eliminar en "Usuarios")
def actualizar_usuarios_db(df_nuevo):
    try:
        conn.update(worksheet="Usuarios", data=df_nuevo)
        st.cache_data.clear() # Limpiamos caché para ver cambios al instante
        return True
    except Exception as e:
        st.error(f"Error actualizando usuarios: {e}")
        return False

# --- CONSTANTES ---
PASSWORD_ADMIN = "entrenadora123" # ¡Cambia esto si quieres!

# --- LÓGICA DE PLANIFICACIÓN ---
def obtener_plan(fase, nivel, dia_semana):
    fisico, tecnico, calentamiento = [], [], []
    es_avanzado = "6-10" in nivel
    
    # 1. Calentamiento según Fase
    if fase == "Fase Competitiva (May-Jun / Nov)":
        calentamiento = ["Cardio Suave (10 min)", "Flexibilidad Dinámica (10 min)", "Básicos de Forma (10 min)"]
    elif fase == "Fase Carga (Mar-Abr / Sep-Oct)":
        calentamiento = ["Termogénico Explosivo (5 min)", "Movilidad Balística (5 min)", "Activación Neural (5 min)"]
    else: # Fase Base
        calentamiento = ["Cardio Progresivo (5 min)", "Movilidad Articular (5 min)", "Postura (5 min)"]

    # 2. Rutinas por Día
    if dia_semana == "Monday":
        foco = "Salto y Potencia Piernas"
        if fase == "Fase Base (Feb/Ago)":
            fisico = ["Sentadillas (3x20)", "Saltos Cajón (3x15)", "Wall Sit"]
            tecnico = ["Drills Carrera", "Entrada Flatback", "Salto a la mano"]
        elif fase == "Fase Carga (Mar-Abr / Sep-Oct)":
            fisico = ["Contraste: Sentadilla+Salto", "Saltos Conejo", "Sprints"]
            tecnico = ["Carrera Completa", "Acrobacia Corta", "Volumen Saltos"]
        else: # Competitiva
            fisico = ["Saltos Reactivos (3x5)", "Visualización"]
            tecnico = ["Stick Landings", "Simulacro Salto"]

    elif dia_semana == "Tuesday":
        foco = "Barras y Tracción"
        if fase == "Fase Base (Feb/Ago)":
            fisico = ["Dominadas Asistidas", "Leg Lifts", "Trepa Soga"]
            tecnico = ["Balanceos", "Kip Drill", "Cast Horizontal"]
        elif fase == "Fase Carga (Mar-Abr / Sep-Oct)":
            fisico = ["Kipping Pullups", "V-ups Rápidas", "Aguante 1 mano"]
            tecnico = ["Conexiones", "Mitades de Rutina", "Resistencia"]
        else:
            fisico = ["Hollow Body", "Dominadas Explosivas"]
            tecnico = ["Rutinas Completas", "Fluidez"]

    elif dia_semana == "Wednesday":
        foco = "Viga y Core"
        if fase == "Fase Base (Feb/Ago)":
            fisico = ["Hollow/Arch", "Planchas", "Flexibilidad Activa"]
            tecnico = ["Caminatas", "Saltos Básicos", "Acro Sin Vuelo"]
        elif fase == "Fase Carga (Mar-Abr / Sep-Oct)":
            fisico = ["EMOM 40min", "Planchas Inestables"]
            tecnico = ["Series x10", "Pressure Sets"]
        else:
            fisico = ["Ballet", "Saltos Amplitud", "Mental"]
            tecnico = ["Rutinas SIN CAÍDA", "Presentación"]

    elif dia_semana == "Thursday":
        foco = "Suelo y Empuje"
        if fase == "Fase Base (Feb/Ago)":
            fisico = ["Flexiones", "Caminata Manos", "V-ups"]
            tecnico = ["Tumbling Básico", "Ruedas", "Drills Mortal"]
        elif fase == "Fase Carga (Mar-Abr / Sep-Oct)":
            fisico = ["Flexiones Palmada", "Soga Doble", "Balón Medicinal"]
            tecnico = ["Resistencia Líneas", "Rutinas Tumble Trak"]
        else:
            fisico = ["Agilidad", "Sprints", "Coreografía"]
            tecnico = ["Rutinas Música", "Detalles Puntas"]

    elif dia_semana == "Friday":
        foco = "Control / Modelaje"
        if fase == "Fase Competitiva (May-Jun / Nov)":
            fisico = ["Estiramiento", "Rodillo", "Charla"]
            tecnico = ["SIMULACRO JUZGADO", "Rotación Olímpica"]
        else:
            fisico = ["CIRCUITO METABÓLICO", "Burpees/Soga"]
            tecnico = ["Repaso Libre", "Trabajo Debilidades"]
            
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
    
    # Cargar usuarios desde Google Sheets
    df_usuarios = cargar_usuarios_db()
    
    with tab1:
        with st.form("login_gimnasta"):
            dni = st.text_input("Ingresa tu DNI")
            if st.form_submit_button("Entrar", use_container_width=True):
                # Buscar DNI
                usuario_encontrado = df_usuarios[df_usuarios['DNI'] == dni]
                
                if not usuario_encontrado.empty:
                    datos = usuario_encontrado.iloc[0]
                    st.session_state['logueado'] = True
                    st.session_state['es_admin'] = False
                    st.session_state['usuario_actual'] = {
                        "dni": datos['DNI'],
                        "nombre": datos['Nombre'],
                        "nivel": datos['Nivel']
                    }
                    st.rerun()
                else:
                    st.error("DNI no encontrado. Pide a tu entrenadora que te registre.")
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

# --- VISTA ENTRENADORA (ADMIN) ---
def mostrar_dashboard():
    st.title("📊 Panel Entrenadora")
    
    tab_dash, tab_users = st.tabs(["📈 Historial de Entrenamientos", "👥 Gestión de Gimnastas"])
    
    # PESTAÑA 1: HISTORIAL
    with tab_dash:
        df = cargar_historial()
        if df.empty:
            st.info("Aún no hay entrenamientos registrados en la hoja 'Historial'.")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Registros Totales", len(df))
            col2.metric("Último Registro", df.iloc[-1]['Fecha'] if not df.empty else "-")
            
            st.subheader("📋 Últimos Entrenamientos")
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
            st.markdown(f"[Abrir Google Sheet]({st.secrets['connections']['gsheets']['spreadsheet']})")

    # PESTAÑA 2: AGREGAR / ELIMINAR
    with tab_users:
        st.info("Administra aquí quién tiene acceso a la App. Esto actualiza la hoja 'Usuarios'.")
        
        df_usuarios = cargar_usuarios_db()
        st.write("### 📋 Gimnastas Activas")
        st.dataframe(df_usuarios, use_container_width=True)
        
        col_add, col_del = st.columns([1, 1])
        
        # --- AGREGAR ---
        with col_add:
            with st.container(border=True):
                st.subheader("➕ Agregar Nueva")
                with st.form("add_user"):
                    new_dni = st.text_input("DNI (Usuario)")
                    new_name = st.text_input("Nombre y Apellido")
                    new_level = st.selectbox("Nivel", ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"])
                    
                    if st.form_submit_button("Guardar Gimnasta", use_container_width=True):
                        if new_dni and new_name:
                            # Validar duplicados
                            if new_dni in df_usuarios['DNI'].values:
                                st.error("¡Ese DNI ya existe!")
                            else:
                                new_row = pd.DataFrame([{"DNI": new_dni, "Nombre": new_name, "Nivel": new_level}])
                                df_updated = pd.concat([df_usuarios, new_row], ignore_index=True)
                                
                                with st.spinner("Guardando en la nube..."):
                                    if actualizar_usuarios_db(df_updated):
                                        st.success("¡Gimnasta agregada correctamente!")
                                        time.sleep(1)
                                        st.rerun()
                        else:
                            st.warning("Faltan datos.")

        # --- ELIMINAR ---
        with col_del:
            with st.container(border=True):
                st.subheader("🗑️ Eliminar Gimnasta")
                if not df_usuarios.empty:
                    lista_opciones = df_usuarios['DNI'] + " - " + df_usuarios['Nombre']
                    seleccion = st.selectbox("Selecciona a quién dar de baja", lista_opciones)
                    
                    if st.button("Eliminar Seleccionada", type="primary"):
                        dni_borrar = seleccion.split(" - ")[0]
                        df_updated = df_usuarios[df_usuarios['DNI'] != dni_borrar]
                        
                        with st.spinner("Eliminando..."):
                            if actualizar_usuarios_db(df_updated):
                                st.success("¡Gimnasta eliminada!")
                                time.sleep(1)
                                st.rerun()
                else:
                    st.write("No hay usuarios para eliminar.")

# --- VISTA GIMNASTA ---
def mostrar_app_gimnasta():
    user = st.session_state['usuario_actual']
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3048/3048398.png", width=60)
        st.write(f"Hola, **{user['nombre']}**")
        if st.button("Cerrar Sesión"): logout()
        
        st.markdown("---")
        fecha = st.date_input("Fecha", datetime.now())
        
        # Selector de Fase Inteligente (por mes)
        mes = fecha.month
        idx_fase = 0
        if mes in [3, 4, 9, 10]: idx_fase = 1
        elif mes in [5, 6, 11]: idx_fase = 2
        
        fase = st.selectbox("Fase Actual", 
                            ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"],
                            index=idx_fase)

    dia_ing = fecha.strftime("%A")
    plan = obtener_plan(fase, user['nivel'], dia_ing)
    
    if plan['foco'] == "Descanso":
        st.title("😴 Día de Descanso")
        st.info("Recuperación activa. ¡Hidrátate bien!")
    else:
        st.title(f"Plan: {plan['foco']}")
        
        # Métricas de progreso
        completados = 0
        total = len(plan['calentamiento'] + plan['fisico'] + plan['tecnico'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔥 Físico & Calentamiento")
            with st.container(border=True):
                for i in plan['calentamiento'] + plan['fisico']:
                    if st.checkbox(i, key=i): completados += 1
        with col2:
            st.subheader("🤸‍♀️ Técnico")
            with st.container(border=True):
                if "Competitiva" in fase: st.warning("⚠️ Calidad sobre cantidad.")
                for i in plan['tecnico']:
                    if st.checkbox(i, key=i): completados += 1
        
        st.markdown("---")
        notas = st.text_area("Notas / Sensaciones del entrenamiento:")
        
        progreso = completados / total if total > 0 else 0
        st.progress(progreso)
        st.write(f"Progreso: {int(progreso*100)}%")
        
        if st.button("✅ TERMINAR Y GUARDAR", type="primary"):
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
            with st.spinner("Guardando en tu historial..."):
                if guardar_entrenamiento(datos):
                    st.success("¡Entrenamiento registrado con éxito!")
                    st.balloons()
                    time.sleep(2)

# --- EJECUCIÓN PRINCIPAL ---
if not st.session_state['logueado']:
    login()
else:
    if st.session_state['es_admin']:
        mostrar_dashboard()
    else:
        mostrar_app_gimnasta()
