import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema EMGA - Gestión Total", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. GESTIÓN DE LA BASE DE DATOS (LECTURA/ESCRITURA) ---

def cargar_historial():
    try: return conn.read(worksheet="Historial", ttl=0)
    except: return pd.DataFrame()

def cargar_usuarios_db():
    try:
        df = conn.read(worksheet="Usuarios", ttl=0)
        df['DNI'] = df['DNI'].astype(str)
        return df
    except: return pd.DataFrame(columns=["DNI", "Nombre", "Rol", "Nivel_o_Pass", "Activo"])

def cargar_planificacion_db():
    try:
        return conn.read(worksheet="Planificacion", ttl=0)
    except: return pd.DataFrame()

def guardar_entrenamiento(datos):
    try:
        df_ex = cargar_historial()
        df_new = pd.DataFrame([datos])
        df_final = pd.concat([df_ex, df_new], ignore_index=True)
        conn.update(worksheet="Historial", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}"); return False

def actualizar_usuarios_db(df_nuevo):
    try:
        conn.update(worksheet="Usuarios", data=df_nuevo)
        st.cache_data.clear(); return True
    except: return False

def actualizar_planificacion_db(df_nuevo):
    try:
        conn.update(worksheet="Planificacion", data=df_nuevo)
        st.cache_data.clear(); return True
    except: return False

# --- 2. LÓGICA DE PLANIFICACIÓN INTELIGENTE ---

# Esta función verifica si la hoja está vacía. Si lo está, carga el plan base automáticamente.
def inicializar_plan_default():
    df = cargar_planificacion_db()
    if df.empty or len(df) < 5:
        # Generamos una estructura base para evitar errores
        data_base = []
        fases = ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"]
        niveles = ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"]
        dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        for f in fases:
            for n in niveles:
                for d in dias:
                    # Rellenamos con texto genérico para editar luego
                    data_base.append({
                        "Fase": f, "Nivel": n, "Dia": d,
                        "Foco": "Foco del día (Editar)",
                        "Calentamiento": "Trote, galope, saltos tijera y movilidad articular completa.\n1 min Parada de manos (Pared), 1 min Hollow, 1 min Arch.\nEstiramiento dinámico de muñecas y tobillos (CRUCIAL para prevenir lesiones en fase de volumen).",
                        "Fisico": "Ejercicio 1\nEjercicio 2\nEjercicio 3",
                        "Tecnico": "Drill 1\nDrill 2\nRutinas"
                    })
        df_base = pd.DataFrame(data_base)
        actualizar_planificacion_db(df_base)
        return df_base
    return df

def obtener_plan_dinamico(fase, nivel, dia_ingles):
    df_plan = cargar_planificacion_db()
    
    # Si falla la carga, intentamos inicializar
    if df_plan.empty: 
        df_plan = inicializar_plan_default()

    # Filtramos la fila exacta
    filtro = df_plan[
        (df_plan['Fase'] == fase) & 
        (df_plan['Nivel'] == nivel) & 
        (df_plan['Dia'] == dia_ingles)
    ]

    if not filtro.empty:
        fila = filtro.iloc[0]
        # Convertimos los textos con "Enter" en listas para los checkboxes
        return {
            "foco": fila['Foco'],
            "calentamiento": str(fila['Calentamiento']).split('\n'),
            "fisico": str(fila['Fisico']).split('\n'),
            "tecnico": str(fila['Tecnico']).split('\n')
        }
    else:
        # Retorno por defecto si es sábado/domingo o no hay datos
        return {"foco": "Descanso", "calentamiento": [], "fisico": [], "tecnico": []}

# --- 3. GESTIÓN DE SESIÓN ---
if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if 'rol_actual' not in st.session_state: st.session_state['rol_actual'] = ""
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = {}

def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso Equipo</h1>", unsafe_allow_html=True)
    df_usuarios = cargar_usuarios_db()
    
    gimnastas = df_usuarios[df_usuarios['Rol'] == 'Gimnasta']
    entrenadores = df_usuarios[df_usuarios['Rol'] == 'Entrenador']
    
    tab_alum, tab_prof = st.tabs(["Soy Gimnasta 🤸‍♀️", "Soy Entrenador/a 📋"])
    
    with tab_alum:
        with st.form("login_gimnasta"):
            dni = st.text_input("Ingresa tu DNI")
            if st.form_submit_button("Entrar"):
                user = gimnastas[gimnastas['DNI'] == dni]
                if not user.empty and user.iloc[0]['Activo'] == 'SI':
                    datos = user.iloc[0]
                    st.session_state.update({'logueado': True, 'rol_actual': 'Gimnasta', 'usuario_actual': datos.to_dict()})
                    st.rerun()
                else: st.error("Acceso denegado.")

    with tab_prof:
        lista_profes = entrenadores['Nombre'].unique().tolist()
        if lista_profes:
            seleccion = st.selectbox("Nombre:", lista_profes)
            pwd = st.text_input("Contraseña:", type="password")
            if st.button("Ingresar Admin"):
                profe = entrenadores[entrenadores['Nombre'] == seleccion].iloc[0]
                if pwd == str(profe['Nivel_o_Pass']):
                    st.session_state.update({'logueado': True, 'rol_actual': 'Entrenador', 'usuario_actual': profe.to_dict()})
                    st.rerun()
                else: st.error("Incorrecto.")

def logout():
    st.session_state.clear()
    st.rerun()

# --- 4. PANEL DE ENTRENADOR (ADMIN) ---
def mostrar_dashboard():
    st.title(f"📋 Panel de Gestión - {st.session_state['usuario_actual']['Nombre']}")
    
    # TRES PESTAÑAS AHORA
    tab_stats, tab_edit_plan, tab_users = st.tabs(["📊 Historial", "✏️ Editar Entrenamientos", "👥 Usuarios"])
    
    # --- PESTAÑA 1: ESTADÍSTICAS ---
    with tab_stats:
        df = cargar_historial()
        if not df.empty:
            st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)
            st.markdown(f"[Ver en Google Sheets]({st.secrets['connections']['gsheets']['spreadsheet']})")
        else: st.info("Sin registros.")

    # --- PESTAÑA 2: EDITOR DE PLANIFICACIÓN (NUEVO) ---
    with tab_edit_plan:
        st.info("💡 Selecciona Fase, Nivel y Día para cargar el plan y modificarlo.")
        
        col_sel1, col_sel2, col_sel3 = st.columns(3)
        with col_sel1:
            fase_edit = st.selectbox("1. Fase", ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"])
        with col_sel2:
            nivel_edit = st.selectbox("2. Nivel", ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"])
        with col_sel3:
            dia_traduccion = {"Lunes": "Monday", "Martes": "Tuesday", "Miércoles": "Wednesday", "Jueves": "Thursday", "Viernes": "Friday"}
            dia_espanol = st.selectbox("3. Día", list(dia_traduccion.keys()))
            dia_edit = dia_traduccion[dia_espanol]

        # Cargar datos actuales
        df_plan = cargar_planificacion_db()
        if df_plan.empty: df_plan = inicializar_plan_default()

        # Filtrar fila actual
        filtro_idx = df_plan[
            (df_plan['Fase'] == fase_edit) & 
            (df_plan['Nivel'] == nivel_edit) & 
            (df_plan['Dia'] == dia_edit)
        ].index

        if not filtro_idx.empty:
            idx = filtro_idx[0]
            datos_actuales = df_plan.loc[idx]

            st.markdown("---")
            with st.form("editor_plan"):
                st.subheader(f"Editando: {dia_espanol} - {nivel_edit}")
                
                # Campos de edición
                new_foco = st.text_input("Objetivo / Foco del Día", value=datos_actuales['Foco'])
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**🔥 Calentamiento** (1 por línea)")
                    new_cal = st.text_area("Lista", value=datos_actuales['Calentamiento'], height=200)
                with c2:
                    st.markdown("**💪 Físico** (1 por línea)")
                    new_fis = st.text_area("Lista", value=datos_actuales['Fisico'], height=200)
                with c3:
                    st.markdown("**🤸‍♀️ Técnico** (1 por línea)")
                    new_tec = st.text_area("Lista", value=datos_actuales['Tecnico'], height=200)
                
                if st.form_submit_button("💾 Guardar Cambios"):
                    # Actualizar DataFrame localmente
                    df_plan.at[idx, 'Foco'] = new_foco
                    df_plan.at[idx, 'Calentamiento'] = new_cal
                    df_plan.at[idx, 'Fisico'] = new_fis
                    df_plan.at[idx, 'Tecnico'] = new_tec
                    
                    # Subir a Google Sheets
                    with st.spinner("Actualizando base de datos..."):
                        if actualizar_planificacion_db(df_plan):
                            st.success("¡Plan actualizado correctamente!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.warning("No se encontró una fila para esta configuración. (Ejecuta la app una vez para crear la base).")

    # --- PESTAÑA 3: USUARIOS ---
    with tab_users:
        # (Código de usuarios resumido, igual que antes)
        df_users = cargar_usuarios_db()
        st.dataframe(df_users, use_container_width=True)
        with st.form("add_user"):
            c1, c2, c3 = st.columns(3)
            d = c1.text_input("DNI")
            n = c2.text_input("Nombre")
            r = c3.selectbox("Rol", ["Gimnasta", "Entrenador"])
            p = st.text_input("Nivel / Password")
            if st.form_submit_button("Agregar"):
                new = pd.DataFrame([{"DNI":d, "Nombre":n, "Rol":r, "Nivel_o_Pass":p, "Activo":"SI"}])
                if actualizar_usuarios_db(pd.concat([df_users, new], ignore_index=True)):
                    st.rerun()

# --- 5. VISTA GIMNASTA ---
def mostrar_app_gimnasta():
    user = st.session_state['usuario_actual']
    with st.sidebar:
        st.write(f"Hola, **{user['Nombre']}**"); st.caption(user['Nivel_o_Pass'])
        if st.button("Salir"): logout()
        fecha = st.date_input("Fecha", datetime.now())
        fase = st.selectbox("Fase", ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"])

    dia_ing = fecha.strftime("%A")
    # AQUI LLAMAMOS AL PLAN DINÁMICO
    plan = obtener_plan_dinamico(fase, user['Nivel_o_Pass'], dia_ing)

    if plan['foco'] == "Descanso":
        st.info("Día de descanso.")
    else:
        st.title(f"Plan: {plan['foco']}")
        completados = 0
        lista_total = plan['calentamiento'] + plan['fisico'] + plan['tecnico']
        total = len([x for x in lista_total if x.strip() != ""]) # Contar solo items no vacíos
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Físico"); 
            for i in plan['calentamiento'] + plan['fisico']: 
                if i.strip(): 
                    if st.checkbox(i, key=i): completados+=1
        with c2:
            st.subheader("Técnico"); 
            for i in plan['tecnico']: 
                if i.strip():
                    if st.checkbox(i, key=i): completados+=1
        
        progreso = completados/total if total>0 else 0
        st.progress(progreso)
        
        if st.button("Guardar"):
            datos = {"Fecha":str(fecha), "Atleta":user['Nombre'], "Foco":plan['foco'], "Cumplimiento":f"{int(progreso*100)}%"}
            if guardar_entrenamiento(datos): st.success("Guardado!"); time.sleep(1)

# --- MAIN ---
if not st.session_state['logueado']: login()
else:
    if st.session_state['rol_actual'] == 'Entrenador': mostrar_dashboard()
    else: mostrar_app_gimnasta()


