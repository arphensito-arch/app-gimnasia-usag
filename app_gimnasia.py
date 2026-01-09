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
        profes = df_u[df_u['Rol'] == 'Entrenador']
        sel = st.selectbox("Profesor/a:", profes['Nombre'].tolist())
        pwd = st.text_input("Clave:", type="password")
        if st.button("Acceso Admin"):
            p_data = profes[profes['Nombre'] == sel].iloc[0]
            if pwd == str(p_data['Nivel_o_Pass']):
                st.session_state.update({'logueado': True, 'rol': 'Entrenador', 'user': p_data.to_dict()})
                st.rerun()

# --- 4. VISTA ENTRENADOR ---
def vista_admin():
    st.title(f"📋 Panel: {st.session_state['user']['Nombre']}")
    t1, t2, t3 = st.tabs(["📊 Historial", "✏️ Editor de Plan", "👥 Usuarios"])
    
    with t2:
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

    with t1:
        df_h = conn.read(worksheet="Historial", ttl=0)
        st.dataframe(df_h, use_container_width=True)

    with t3:
        st.write("Gestión de Usuarios")
        # Aquí puedes agregar el código de agregar/eliminar usuarios si lo deseas.

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
