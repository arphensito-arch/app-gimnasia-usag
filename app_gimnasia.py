import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="USAG Gestión Profesional", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. FUNCIONES DE BASE DE DATOS ---

def cargar_usuarios_db():
    try:
        df = conn.read(worksheet="Usuarios", ttl=0)
        df['DNI'] = df['DNI'].astype(str)
        return df
    except: return pd.DataFrame(columns=["DNI", "Nombre", "Rol", "Nivel_o_Pass", "Activo"])

def cargar_planificacion_db():
    try: return conn.read(worksheet="Planificacion", ttl=0)
    except: return pd.DataFrame()

def actualizar_planificacion_db(df_nuevo):
    try:
        conn.update(worksheet="Planificacion", data=df_nuevo)
        st.cache_data.clear()
        return True
    except: return False

def guardar_registro(datos, hoja):
    try:
        df_ex = conn.read(worksheet=hoja, ttl=0)
        df_final = pd.concat([df_ex, pd.DataFrame([datos])], ignore_index=True)
        conn.update(worksheet=hoja, data=df_final)
        return True
    except: return False

# --- 2. INICIALIZADOR TÉCNICO (Alinea la App con el Plan Original) ---
def inicializar_plan_si_vacio():
    df = cargar_planificacion_db()
    if df.empty or len(df) < 5:
        with st.spinner("Configurando Plan Técnico USAG..."):
            data_base = []
            fases = ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"]
            niveles = ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"]
            dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

            for f in fases:
                for n in niveles:
                    es_av = "6-10" in n
                    for d in dias:
                        foco, cal, fis, tec = "", "", "", ""
                        if d == "Monday":
                            foco = "Salto y Potencia"
                            cal = "Trote 5'\nMovilidad\nHollow/Arch"
                            fis = "Sentadillas\nSaltos Cajón" if not es_av else "Sentadilla Lastre\nDepth Jumps"
                            tec = "Carrera Drills\nFlatback" if not es_av else "Yurchenko Drills\nRechazo"
                        elif d == "Tuesday":
                            foco = "Barras y Tracción"
                            cal = "Hombros\nMuñecas\nHandstand"
                            fis = "Dominadas\nLeg Lifts" if not es_av else "Trepa en L\nToes-to-bar"
                            tec = "Balanceos\nKip Drills" if not es_av else "Gigantes\nCast Vertical"
                        elif d == "Wednesday":
                            foco = "Viga y Core"
                            cal = "Caminatas\nSaltos"
                            fis = "Hollow Rocks\nPlanchas"
                            tec = "Verticales\nEquilibrios" if not es_av else "Series Acro\nGiros"
                        elif d == "Thursday":
                            foco = "Suelo y Empuje"
                            cal = "Push-ups técnica"
                            fis = "Flexiones\nCaminata Manos"
                            tec = "Rondada Drills\nMortal Drills"
                        elif d == "Friday":
                            foco = "Control / Modelaje"
                            cal = "Movilidad"
                            fis = "Circuito Metabólico"
                            tec = "Aparato Débil" if "Base" in f else "Simulacro"
                        
                        data_base.append({"Fase": f, "Nivel": n, "Dia": d, "Foco": foco, "Calentamiento": cal, "Fisico": fis, "Tecnico": tec})
            
            df_base = pd.DataFrame(data_base)
            actualizar_planificacion_db(df_base)
            return df_base
    return df

# --- 3. GESTIÓN DE SESIÓN ---
if 'logueado' not in st.session_state: st.session_state['logueado'] = False

def login():
    st.title("🔐 Acceso USAG")
    df_u = cargar_usuarios_db()
    t1, t2 = st.tabs(["Gimnastas", "Entrenadores"])
    
    with t1:
        dni = st.text_input("DNI")
        if st.button("Entrar"):
            user = df_u[(df_u['DNI'] == dni) & (df_u['Rol'] == 'Gimnasta')]
            if not user.empty:
                st.session_state.update({'logueado': True, 'rol': 'Gimnasta', 'user': user.iloc[0].to_dict()})
                st.rerun()
    with t2:
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
        st.subheader("Modificar Entrenamiento Diario")
        f_ed = st.selectbox("Fase", ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"])
        n_ed = st.selectbox("Nivel", ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"])
        d_ed = st.selectbox("Día", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        df_p = inicializar_plan_si_vacio()
        idx = df_p[(df_p['Fase'] == f_ed) & (df_p['Nivel'] == n_ed) & (df_p['Dia'] == d_ed)].index
        
        if not idx.empty:
            row = df_p.loc[idx[0]]
            with st.form("edit"):
                foc = st.text_input("Foco", row['Foco'])
                c1, c2, c3 = st.columns(3)
                ca = c1.text_area("Calentamiento", row['Calentamiento'])
                fi = c2.text_area("Físico", row['Fisico'])
                te = c3.text_area("Técnico", row['Tecnico'])
                if st.form_submit_button("Guardar Cambios"):
                    df_p.at[idx[0], 'Foco'], df_p.at[idx[0], 'Calentamiento'] = foc, ca
                    df_p.at[idx[0], 'Fisico'], df_p.at[idx[0], 'Tecnico'] = fi, te
                    if actualizar_planificacion_db(df_p): st.success("¡Plan Actualizado!"); time.sleep(1); st.rerun()

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
def vista_gimnasta():
    u = st.session_state['user']
    st.title(f"Hola {u['Nombre']}! 🤸‍♀️")
    
    with st.sidebar:
        if st.button("Cerrar Sesión"): st.session_state.clear(); st.rerun()
        fecha = st.date_input("Fecha", datetime.now())
        fase = st.selectbox("Fase", ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"])

    # Cargar Plan
    df_p = inicializar_plan_si_vacio()
    dia = fecha.strftime("%A")
    plan_row = df_p[(df_p['Fase'] == fase) & (df_p['Nivel'] == u['Nivel_o_Pass']) & (df_p['Dia'] == dia)]

    if plan_row.empty or dia in ["Saturday", "Sunday"]:
        st.info("Hoy es día de descanso o recuperación.")
    else:
        p = plan_row.iloc[0]
        st.header(f"Hoy: {p['Foco']}")
        
        # ASISTENCIA RÁPIDA
        if st.button("📍 MARCAR PRESENTE"):
            asistencia = {"Fecha": str(fecha), "Nombre": u['Nombre'], "Asistencia": "Presente"}
            if guardar_registro(asistencia, "Historial"): st.success("¡Asistencia marcada!")

        st.markdown("---")
        c1, c2 = st.columns(2)
        items = p['Calentamiento'].split('\n') + p['Fisico'].split('\n') + p['Tecnico'].split('\n')
        items = [i for i in items if i.strip()]
        
        comp = 0
        with c1:
            st.subheader("Calentamiento / Físico")
            for i in p['Calentamiento'].split('\n') + p['Fisico'].split('\n'):
                if i.strip() and st.checkbox(i): comp += 1
        with c2:
            st.subheader("Técnico")
            for i in p['Tecnico'].split('\n'):
                if i.strip() and st.checkbox(i): comp += 1
        
        prog = comp/len(items) if items else 0
        st.progress(prog)
        if st.button("✅ GUARDAR ENTRENAMIENTO"):
            res = {"Fecha": str(fecha), "Nombre": u['Nombre'], "Cumplimiento": f"{int(prog*100)}%"}
            if guardar_registro(res, "Historial"): st.balloons(); st.success("¡Guardado!")

# --- MAIN ---
if not st.session_state['logueado']: login()
elif st.session_state['rol'] == 'Entrenador': vista_admin()
else: vista_gimnasta()

