import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema USAG - Gestión", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_historial():
    try:
        return conn.read(worksheet="Historial", ttl=0)
    except:
        return pd.DataFrame()

def cargar_usuarios_db():
    try:
        df = conn.read(worksheet="Usuarios", ttl=0)
        df['DNI'] = df['DNI'].astype(str)
        # Filtramos solo los que dicen "SI" en la columna Activo (opcional, pero recomendado)
        return df
    except Exception as e:
        st.error(f"Error leyendo usuarios. Revisa los encabezados en Google Sheets: {e}")
        return pd.DataFrame(columns=["DNI", "Nombre", "Rol", "Nivel_o_Pass", "Activo"])

def guardar_entrenamiento(datos):
    try:
        df_existente = cargar_historial()
        df_nuevo = pd.DataFrame([datos])
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        conn.update(worksheet="Historial", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def actualizar_usuarios_db(df_nuevo):
    try:
        conn.update(worksheet="Usuarios", data=df_nuevo)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error actualizando usuarios: {e}")
        return False

# --- LÓGICA DEL PLAN DE ENTRENAMIENTO ---
def obtener_plan(fase, nivel, dia_semana):
    fisico, tecnico, calentamiento = [], [], []
    
    # Lógica base (Resumida para el ejemplo)
    if fase == "Fase Competitiva":
        calentamiento = ["Cardio Suave (10')", "Flexibilidad (10')", "Básicos (10')"]
    else:
        calentamiento = ["Cardio (5')", "Movilidad (5')", "Postura (5')"]

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
if 'rol_actual' not in st.session_state: st.session_state['rol_actual'] = ""
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = {}

def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso USAG</h1>", unsafe_allow_html=True)
    
    # Cargamos la base de datos completa
    df_usuarios = cargar_usuarios_db()
    
    # Separamos en dos grupos
    gimnastas = df_usuarios[df_usuarios['Rol'] == 'Gimnasta']
    entrenadores = df_usuarios[df_usuarios['Rol'] == 'Entrenador']
    
    tab_alum, tab_prof = st.tabs(["Soy Gimnasta 🤸‍♀️", "Soy Entrenador/a 📋"])
    
    # --- LOGIN GIMNASTAS ---
    with tab_alum:
        with st.form("login_gimnasta"):
            st.write("Ingresa tu documento:")
            dni = st.text_input("DNI")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = gimnastas[gimnastas['DNI'] == dni]
                if not user.empty:
                    datos = user.iloc[0]
                    if datos['Activo'] == 'SI':
                        st.session_state['logueado'] = True
                        st.session_state['rol_actual'] = "Gimnasta"
                        st.session_state['usuario_actual'] = {
                            "dni": datos['DNI'], "nombre": datos['Nombre'], "nivel": datos['Nivel_o_Pass']
                        }
                        st.rerun()
                    else:
                        st.error("Usuario inactivo.")
                else:
                    st.error("DNI no encontrado.")

    # --- LOGIN ENTRENADORES (LISTA DESPLEGABLE) ---
    with tab_prof:
        # Creamos una lista de nombres para el SelectBox
        lista_nombres_profes = entrenadores['Nombre'].unique().tolist()
        
        if not lista_nombres_profes:
            st.warning("No hay entrenadores registrados en la base de datos.")
        else:
            seleccion_profe = st.selectbox("Selecciona tu nombre:", lista_nombres_profes)
            password_input = st.text_input("Contraseña:", type="password")
            
            if st.button("Ingresar como Entrenador", use_container_width=True):
                # Buscamos al profe seleccionado
                profe_data = entrenadores[entrenadores['Nombre'] == seleccion_profe].iloc[0]
                
                # Validamos contraseña (Columna Nivel_o_Pass)
                # Convertimos a string por si es número en excel
                pass_real = str(profe_data['Nivel_o_Pass']) 
                
                if password_input == pass_real:
                    st.session_state['logueado'] = True
                    st.session_state['rol_actual'] = "Entrenador"
                    st.session_state['usuario_actual'] = {
                        "dni": profe_data['DNI'], "nombre": profe_data['Nombre'], "nivel": "Coach"
                    }
                    st.success(f"Hola {profe_data['Nombre']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")

def logout():
    st.session_state['logueado'] = False
    st.session_state['rol_actual'] = ""
    st.rerun()

# --- VISTA: PANEL DE GESTIÓN (SOLO ENTRENADORES) ---
def mostrar_dashboard():
    st.title(f"📋 Panel de Gestión - {st.session_state['usuario_actual']['nombre']}")
    
    tab_stats, tab_users = st.tabs(["📊 Estadísticas", "👥 Gestión de Usuarios"])
    
    with tab_stats:
        df = cargar_historial()
        if df.empty:
            st.info("Sin registros aún.")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Entrenamientos Totales", len(df))
            col2.metric("Último", df.iloc[-1]['Fecha'] if not df.empty else "-")
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)

    with tab_users:
        st.info("Aquí puedes crear GIMNASTAS o nuevos ENTRENADORES.")
        
        df_usuarios = cargar_usuarios_db()
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("### ➕ Agregar Nuevo Usuario")
        
        with st.form("nuevo_usuario"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_dni = st.text_input("DNI (Usuario único)")
                new_nombre = st.text_input("Nombre Completo")
                new_rol = st.selectbox("Rol", ["Gimnasta", "Entrenador"])
            
            with col_b:
                st.write("Dependiendo del Rol:")
                # Usamos un text_input genérico, la etiqueta cambia visualmente
                new_dato = st.text_input("Nivel (si es Gimnasta) o Contraseña (si es Profe)")
                
            if st.form_submit_button("Guardar Usuario"):
                if new_dni and new_nombre and new_dato:
                    if new_dni in df_usuarios['DNI'].values:
                        st.error("¡El DNI ya existe!")
                    else:
                        nuevo = pd.DataFrame([{
                            "DNI": new_dni,
                            "Nombre": new_nombre,
                            "Rol": new_rol,
                            "Nivel_o_Pass": new_dato,
                            "Activo": "SI"
                        }])
                        df_updated = pd.concat([df_usuarios, nuevo], ignore_index=True)
                        if actualizar_usuarios_db(df_updated):
                            st.success(f"{new_rol} agregado correctamente.")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.warning("Completa todos los campos.")

# --- VISTA: APP GIMNASTA (IGUAL QUE ANTES) ---
def mostrar_app_gimnasta():
    user = st.session_state['usuario_actual']
    with st.sidebar:
        st.write(f"Hola, **{user['nombre']}**")
        st.caption(f"Nivel: {user['nivel']}")
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
        
        if st.button("Guardar Entrenamiento", type="primary"):
            datos = {
                "Fecha": str(fecha), "Hora": datetime.now().strftime("%H:%M"),
                "DNI": user['dni'], "Atleta": user['nombre'],
                "Nivel": user['nivel'], "Fase": fase, "Foco": plan['foco'],
                "Cumplimiento": f"{int(progreso * 100)}%", "Notas": notas
            }
            if guardar_entrenamiento(datos):
                st.success("Guardado!")
                time.sleep(2)

# --- MAIN ---
if not st.session_state['logueado']:
    login()
else:
    if st.session_state['rol_actual'] == "Entrenador":
        mostrar_dashboard()
    else:
        mostrar_app_gimnasta()
