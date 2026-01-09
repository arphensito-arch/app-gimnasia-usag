import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema USAG - Planificación Alineada", page_icon="🤸‍♀️", layout="wide")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- GESTIÓN DE BASE DE DATOS ---

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
    try: return conn.read(worksheet="Planificacion", ttl=0)
    except: return pd.DataFrame()

def actualizar_planificacion_db(df_nuevo):
    try:
        conn.update(worksheet="Planificacion", data=df_nuevo)
        st.cache_data.clear()
        return True
    except: return False

# --- FUNCIÓN CRUCIAL: ALINEACIÓN CON EL PLAN ORIGINAL ---
def inicializar_plan_alineado():
    """
    Esta función inyecta las tablas que desarrollamos (Fase Base, Carga y Comp)
    directamente en la hoja de Google Sheets si esta se encuentra vacía.
    """
    df = cargar_planificacion_db()
    if df.empty or len(df) < 5:
        st.warning("Inicializando base de datos con el plan técnico desarrollado...")
        data_base = []
        fases = ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"]
        niveles = ["Desarrollo (Nivel 3-5)", "Opcional/Elite (Nivel 6-10)"]
        dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        for f in fases:
            for n in niveles:
                es_avanzado = "6-10" in n
                for d in dias:
                    # Lógica de alineación según lo desarrollado previamente
                    foco, cal, fis, tec = "", "", "", ""
                    
                    if d == "Monday":
                        foco = "Salto y Potencia de Piernas"
                        if "Base" in f:
                            cal = "Trote 5'\nMovilidad Articular\nHollow/Arch/Handstand"
                            fis = "Sentadillas Profundas\nZancadas\nSaltos al Cajón\nWall Sit" if not es_avanzado else "Sentadilla con Lastre\nPeso Muerto\nDepth Jumps\nWall Sit con Disco"
                            tec = "Drills de Carrera\nEntrada Flatback\nSalto a parada de manos" if not es_avanzado else "Sprints con liga\nEntrada Yurchenko\nRechazo en mesa"
                        elif "Carga" in f:
                            cal = "Sprints cortos\nSaltos laterales\nActivación Neural"
                            fis = "Contraste: Sentadilla+Salto\nSaltos de Conejo\nSprints Suicidas"
                            tec = "Carrera completa con tabla\n20 Saltos de Calidad"
                        else: # Comp
                            cal = "Cardio suave 10'\nFlexibilidad dinámica"
                            fis = "Saltos Reactivos (3x5)\nVisualización"
                            tec = "Stick Landings (Clavar)\n1 Salto Puntuado"

                    elif d == "Tuesday":
                        foco = "Barras y Tracción"
                        if "Base" in f:
                            cal = "Movilidad Hombros\nMuñecas\nHandstand pared"
                            fis = "Dominadas Asistidas\nLeg Lifts\nTrepa de Soga" if not es_avanzado else "Dominadas Estrictas\nToes-to-Bar\nTrepa en L"
                            tec = "Balanceos (Swings)\nKip Drills\nCast horizontal" if not es_avanzado else "Gigantes Correa\nCast Vertical\nSueltas en foso"
                        elif "Carga" in f:
                            cal = "Sprints\nKicks rápidos"
                            fis = "Kipping Pullups\nV-ups Rápidos\nAguante 1 mano"
                            tec = "Conexiones (Kip+Cast)\nMitades de Rutina"
                        else: # Comp
                            cal = "Flexibilidad\nBásicos Forma"
                            fis = "Hollow Body (3x20s)\nDominadas Explosivas"
                            tec = "Rutinas Completas\nSalidas Clavadas"

                    elif d == "Wednesday":
                        foco = "Viga y Core/Flex"
                        if "Base" in f:
                            cal = "Caminatas Relevé\nSaltos Básicos"
                            fis = "Hollow Rocks\nPlancha Lateral\nKicks (Patadas)"
                            tec = "Equilibrios 30s\nVerticales Marcadas"
                        elif "Carga" in f:
                            cal = "HIIT 5'\nSalto soga"
                            fis = "EMOM 40min (Burpees/V-ups)\nPlanchas Bosu"
                            tec = "Series Acrobáticas x10\nPressure Sets"
                        else: # Comp
                            cal = "Danza Viga\nFlexibilidad"
                            fis = "Ballet Suelo\nVisualización"
                            tec = "Rutinas SIN CAÍDA\nPresentación"

                    elif d == "Thursday":
                        foco = "Suelo y Empuje"
                        if "Base" in f:
                            cal = "Círculos brazos\nPush-ups técnica"
                            fis = "Flexiones Codos Pegados\nCaminata Manos\nV-ups"
                            tec = "Rondada Flic-Flac Drills\nVertical Puente"
                        elif "Carga" in f:
                            cal = "Burpees\nSnap downs"
                            fis = "Flexiones Palmada\nSoga Doble\nBalón Medicinal"
                            tec = "Resistencia Líneas\nRutinas Tumble Trak"
                        else: # Comp
                            cal = "Coreografía\nSaltos Amplitud"
                            fis = "Escalera Agilidad\nSprints 15m"
                            tec = "Rutinas Música\nDetalle Puntas"

                    elif d == "Friday":
                        foco = "Control y Modelaje"
                        if "Base" in f:
                            cal = "Movilidad general"
                            fis = "Circuito Metabólico (4 vueltas)"
                            tec = "Repaso aparato débil"
                        elif "Carga" in f:
                            cal = "Trote rápido"
                            fis = "Preventivo Tobillos/Hombros"
                            tec = "Testeo Dificultades\nUnión de Partes"
                        else: # Comp
                            cal = "Calentamiento Torneo"
                            fis = "Descarga/Rodillo"
                            tec = "SIMULACRO JUZGADO\nRotación Olímpica"

                    data_base.append({
                        "Fase": f, "Nivel": n, "Dia": d, "Foco": foco,
                        "Calentamiento": cal, "Fisico": fis, "Tecnico": tec
                    })
        
        df_base = pd.DataFrame(data_base)
        actualizar_planificacion_db(df_base)
        return df_base
    return df

# --- VISTAS Y LÓGICA DE USUARIO ---

def obtener_plan_dinamico(fase, nivel, dia_ingles):
    df_plan = cargar_planificacion_db()
    if df_plan.empty: df_plan = inicializar_plan_alineado()
    
    filtro = df_plan[(df_plan['Fase'] == fase) & (df_plan['Nivel'] == nivel) & (df_plan['Dia'] == dia_ingles)]
    
    if not filtro.empty:
        fila = filtro.iloc[0]
        return {
            "foco": fila['Foco'],
            "calentamiento": str(fila['Calentamiento']).split('\n'),
            "fisico": str(fila['Fisico']).split('\n'),
            "tecnico": str(fila['Tecnico']).split('\n')
        }
    return {"foco": "Descanso", "calentamiento": [], "fisico": [], "tecnico": []}

# (El resto del código del Main, Login y Dashboard se mantiene igual, 
# pero asegúrate de que la función inicializar_plan_alineado sea llamada)

# ... [Login y Logout igual que la versión anterior] ...

def mostrar_dashboard():
    st.title(f"📋 Gestión - {st.session_state['usuario_actual']['Nombre']}")
    tab_stats, tab_edit_plan, tab_users = st.tabs(["📊 Historial", "✏️ Editar Plan", "👥 Usuarios"])
    
    with tab_edit_plan:
        # Aquí se fuerza la carga del plan alineado si el profe entra y no hay nada
        df_plan = inicializar_plan_alineado() 
        # [Lógica de edición del mensaje anterior] ...

def mostrar_app_gimnasta():
    user = st.session_state['usuario_actual']
    with st.sidebar:
        st.write(f"Hola, **{user['Nombre']}**")
        if st.button("Salir"): st.session_state.clear(); st.rerun()
        fecha = st.date_input("Fecha", datetime.now())
        
        # Inteligencia de Fase
        mes = fecha.month
        idx_fase = 0
        if mes in [3, 4, 9, 10]: idx_fase = 1
        elif mes in [5, 6, 11]: idx_fase = 2
        fase = st.selectbox("Fase", ["Fase Base (Feb/Ago)", "Fase Carga (Mar-Abr / Sep-Oct)", "Fase Competitiva (May-Jun / Nov)"], index=idx_fase)

    dia_ing = fecha.strftime("%A")
    plan = obtener_plan_dinamico(fase, user['Nivel_o_Pass'], dia_ing)
    
    if plan['foco'] == "Descanso":
        st.info("Día de descanso.")
    else:
        st.title(f"Plan: {plan['foco']}")
        # [Lógica de checkboxes del mensaje anterior] ...
