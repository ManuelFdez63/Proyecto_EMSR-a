import streamlit as st
import pandas as pd
import numpy as np
import os

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Sistema de Gestión de Capacidad y Tarifas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para mejorar la interfaz visual durante la presentación
st.markdown("""
    <style>
    .main-title {
        font-size: 38px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 18px;
        color: #4B5563;
        margin-bottom: 25px;
    }
    .metric-box {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Sistema de Control de Capacidad y Tarifas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Modelo de simulación interactiva para optimización de Revenue Management</div>', unsafe_allow_html=True)

# --- CARGA DE DATOS ---
csv_filename = 'DatosProyecto.csv'

# Verificamos si existe el archivo; si no, creamos un set de datos por defecto para evitar errores en la demo
if os.path.exists(csv_filename):
    df_base = pd.read_csv(csv_filename, sep=';')
else:
    # Set de datos de ejemplo si el CSV no está en la misma carpeta temporalmente
    data = {
        'Clases': ['A', 'B', 'C', 'D', 'E'],
        'Tarifa': [150, 110, 85, 55, 30]
    }
    df_base = pd.DataFrame(data)
    st.sidebar.warning(f"⚠️ '{csv_filename}' no encontrado. Cargados datos por defecto para la presentación.")

Clases_ = df_base['Clases'].tolist()
Tarifas = tuple(df_base['Tarifa'])

# --- INICIALIZACIÓN DEL ESTADO (SESSION STATE) ---
# Streamlit se ejecuta de arriba a abajo en cada interacción; usamos st.session_state para mantener los datos vivos
if 'plazas_vendidas' not in st.session_state:
    st.session_state.plazas_vendidas = 0
if 'Historial_ventas' not in st.session_state:
    st.session_state.Historial_ventas = np.zeros(len(Clases_))
if 'Clases_actuales' not in st.session_state:
    st.session_state.Clases_actuales = df_base['Clases'].tolist()
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- CONFIGURACIÓN DE PARÁMETROS Y CONSTANTES ---
Cap = 350
C_E = 114
C_D = 31
C_C = 20
C_B = 6
C_A = 0

# --- PANEL LATERAL DE CONTROL ---
st.sidebar.header("⚙️ Parámetros del Sistema")
st.sidebar.markdown(f"**Capacidad Máxima (Cap):** `{Cap}`")
st.sidebar.markdown("---")
st.sidebar.subheader("Protecciones / Umbrales")
st.sidebar.text(f"Umbral E (C_E): {C_E}")
st.sidebar.text(f"Umbral D (C_D): {C_D}")
st.sidebar.text(f"Umbral C (C_C): {C_C}")
st.sidebar.text(f"Umbral B (C_B): {C_B}")
st.sidebar.text(f"Umbral A (C_A): {C_A}")

# Botón para reiniciar la simulación limpiamente
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reiniciar Simulación", type="secondary", use_container_width=True):
    st.session_state.plazas_vendidas = 0
    st.session_state.Historial_ventas = np.zeros(len(Clases_))
    st.session_state.Clases_actuales = df_base['Clases'].tolist()
    st.session_state.logs = ["Simulación reiniciada correctamente."]
    st.rerun()

# --- MÉTRICAS PRINCIPALES (KPIs) ---
recaudado_total = np.sum(st.session_state.Historial_ventas * np.array(Tarifas))
asientos_disponibles = Cap - st.session_state.plazas_vendidas

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric(label="Plazas Vendidas", value=f"{st.session_state.plazas_vendidas} / {Cap}", delta=f"{asientos_disponibles} libres")
with m_col2:
    st.metric(label="Recaudación Total", value=f"{recaudado_total:,.2f} €")
with m_col3:
    st.metric(label="Umbral de Capacidad", value=f"{asientos_disponibles}")
with m_col4:
    clases_activas_str = ", ".join(st.session_state.Clases_actuales) if st.session_state.Clases_actuales else "Ninguna (Cerrado)"
    st.metric(label="Tarifas Disponibles", value=f"{len(st.session_state.Clases_actuales)} activas", delta=clases_activas_str, delta_color="normal")

st.markdown("---")

# --- BLOQUE PRINCIPAL INTERACTIVO ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🛒 Registrar Nueva Solicitud de Venta")
    
    # Reemplazo de los inputs nativos por componentes de Streamlit
    plazas_deseadas = st.number_input("Introduce el número de asientos deseados:", min_value=1, max_value=Cap, value=1, step=1)
    tarifa_deseada = st.selectbox("Introduce la tarifa deseada (A, B, C, D, E):", ['A', 'B', 'C', 'D', 'E'])
    
    if st.button("Procesar Transacción 🚀", type="primary", use_container_width=True):
        # Clonamos el estado actual de manera segura para la lógica transaccional
        plazas_vendidas_calc = st.session_state.plazas_vendidas + plazas_deseadas
        Umbral_calc = Cap - plazas_vendidas_calc
        Clases_calc = st.session_state.Clases_actuales.copy()
        Historial_ventas_calc = st.session_state.Historial_ventas.copy()
        
        # Lista temporal para guardar los prints/mensajes de esta ejecución
        exec_logs = []
        is_error = False
        
        # --- Lógica Algorítmica Original adaptada ---
        if tarifa_deseada not in ['A', 'B', 'C', 'D', 'E']:
            st.error("Error: La tarifa deseada no es válida. Por favor, introduce A, B, C, D o E.")
            is_error = True
        elif plazas_vendidas_calc > Cap:
            st.error(f"Error: La cantidad de asientos vendidos ({plazas_vendidas_calc}) supera la capacidad ({Cap}).")
            is_error = True
        else:
            if Umbral_calc == C_A:
                Clases_calc.clear()
                exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa {tarifa_deseada}")
                Historial_ventas_calc[Clases_.index(tarifa_deseada)] += plazas_deseadas
                exec_logs.append(f"No hay asientos disponibles después de vender todos los asientos.")
                
            elif Umbral_calc < C_B:
                for c in ['B', 'C', 'D', 'E']:
                    if c in Clases_calc: Clases_calc.remove(c)
                if tarifa_deseada == 'A':
                    exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa A")
                    Historial_ventas_calc[Clases_.index('A')] += plazas_deseadas
                    exec_logs.append(f"Tarifas disponibles después de vender {plazas_vendidas_calc} asientos: {Clases_calc}")
                else:
                    st.error("No hay asientos disponibles en esa tarifa.")
                    is_error = True
                    # Volvemos a calcular con el estado previo para los mensajes informativos
                    p_libres_prev = Cap - st.session_state.plazas_vendidas
                    if p_libres_prev - C_B > 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_}")
                        exec_logs.append(f"Quedan {p_libres_prev - C_B} asientos de la tarifa B")
                    elif p_libres_prev - C_B == 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_calc}")
                
                ref_p = plazas_vendidas_calc if not is_error else st.session_state.plazas_vendidas
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_A} de la tarifa A")

            elif Umbral_calc < C_C:
                for c in ['C', 'D', 'E']:
                    if c in Clases_calc: Clases_calc.remove(c)
                if tarifa_deseada in ['A', 'B']:
                    exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa {tarifa_deseada}")
                    Historial_ventas_calc[Clases_.index(tarifa_deseada)] += plazas_deseadas
                    exec_logs.append(f"Tarifas disponibles después de vender {plazas_vendidas_calc} asientos: {Clases_calc}")
                elif tarifa_deseada in ['C', 'D', 'E']:
                    st.error("No hay asientos disponibles en esa tarifa.")
                    is_error = True
                    p_libres_prev = Cap - st.session_state.plazas_vendidas
                    if p_libres_prev - C_C > 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_}")
                        exec_logs.append(f"Quedan {p_libres_prev - C_C} asientos de la tarifa C")
                    elif p_libres_prev - C_C == 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_calc}")

                ref_p = plazas_vendidas_calc if not is_error else st.session_state.plazas_vendidas
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_A} asientos de la tarifa A")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_B} asientos de la tarifa B")

            elif Umbral_calc < C_D:
                for c in ['D', 'E']:
                    if c in Clases_calc: Clases_calc.remove(c)
                if tarifa_deseada in ['A', 'B', 'C']:
                    exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa {tarifa_deseada}")
                    Historial_ventas_calc[Clases_.index(tarifa_deseada)] += plazas_deseadas
                    exec_logs.append(f"Tarifas disponibles después de vender {plazas_vendidas_calc} asientos: {Clases_calc}")
                elif tarifa_deseada in ['D', 'E']:
                    st.error("No hay asientos disponibles en esa tarifa.")
                    is_error = True
                    p_libres_prev = Cap - st.session_state.plazas_vendidas
                    if p_libres_prev - C_D > 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_}")
                        exec_logs.append(f"Quedan {p_libres_prev - C_D} asientos de la tarifa D")
                    elif p_libres_prev - C_D == 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_calc}")

                ref_p = plazas_vendidas_calc if not is_error else st.session_state.plazas_vendidas
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_A} asientos de la tarifa A")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_B} asientos de la tarifa B")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_C} asientos de la tarifa C")

            elif Umbral_calc < C_E:
                if 'E' in Clases_calc: Clases_calc.remove('E')
                if tarifa_deseada in ['A', 'B', 'C', 'D']:
                    exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa {tarifa_deseada}")
                    Historial_ventas_calc[Clases_.index(tarifa_deseada)] += plazas_deseadas
                    exec_logs.append(f"Tarifas disponibles después de vender {plazas_vendidas_calc} asientos: {Clases_calc}")
                elif tarifa_deseada in ['E']:
                    st.error("No hay suficientes asientos disponibles en esa tarifa.")
                    is_error = True
                    p_libres_prev = Cap - st.session_state.plazas_vendidas
                    if p_libres_prev - C_E > 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_}")
                        exec_logs.append(f"Quedan {p_libres_prev - C_E} asientos de la tarifa E")
                    elif p_libres_prev - C_E == 0:
                        exec_logs.append(f"Tarifas disponibles después de vender {st.session_state.plazas_vendidas} asientos: {Clases_calc}")

                ref_p = plazas_vendidas_calc if not is_error else st.session_state.plazas_vendidas
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_A} asientos de la tarifa A")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_B} asientos de la tarifa B")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_C} asientos de la tarifa C")
                exec_logs.append(f"Quedan {(Cap - ref_p) - C_D} asientos de la tarifa D")

            else:
                exec_logs.append(f"Se han vendido {plazas_deseadas} asientos de la tarifa {tarifa_deseada}")
                Historial_ventas_calc[Clases_.index(tarifa_deseada)] += plazas_deseadas
                exec_logs.append(f"Tarifas disponibles después de vender {plazas_vendidas_calc} asientos: {Clases_calc}")
                exec_logs.append(f"Quedan {(Cap - plazas_vendidas_calc) - C_A} asientos de la tarifa A")
                exec_logs.append(f"Quedan {(Cap - plazas_vendidas_calc) - C_B} asientos de la tarifa B")
                exec_logs.append(f"Quedan {(Cap - plazas_vendidas_calc) - C_C} asientos de la tarifa C")
                exec_logs.append(f"Quedan {(Cap - plazas_vendidas_calc) - C_D} asientos de la tarifa D")
                exec_logs.append(f"Quedan {(Cap - plazas_vendidas_calc) - C_E} asientos de la tarifa E")

        # Guardar en estado global si la transacción fue exitosa
        if not is_error:
            st.session_state.plazas_vendidas = plazas_vendidas_calc
            st.session_state.Historial_ventas = Historial_ventas_calc
            st.session_state.Clases_actuales = Clases_calc
            st.session_state.logs = exec_logs
            st.success("¡Transacción procesada correctamente!")
            st.rerun()
        else:
            st.session_state.logs = exec_logs

with col_right:
    st.subheader("🖥️ Asientos disponibles por tarifas")
    if st.session_state.logs:
        for log in st.session_state.logs:
            if "Error" in log or "No hay" in log:
                st.warning(f"• {log}")
            else:
                st.info(f"• {log}")
    else:
        st.write("*Esperando transacciones...*")

# --- BLOQUE DE GRÁFICOS Y MÉTRICAS COMPLEMENTARIAS ---
st.markdown("---")
st.subheader("📊 Cuadro de Mando Visual")

g_col1, g_col2 = st.columns(2)

with g_col1:
    st.markdown("**Cantidad de Billetes Vendidos por Tipo de Tarifa**")
    df_chart = pd.DataFrame({
        'Clase Tarifa': Clases_,
        'Asientos Vendidos': st.session_state.Historial_ventas
    })
    st.bar_chart(df_chart.set_index('Clase Tarifa'), color="#1E3A8A")

with g_col2:
    st.markdown("**Desglose Financiero y de Inventario**")
    recaudado_rama = st.session_state.Historial_ventas * np.array(Tarifas)
    df_summary = pd.DataFrame({
        'Clase': Clases_,
        'Precio Tarifa': [f"{t:.2f} €" for t in Tarifas],
        'Asientos Vendidos': st.session_state.Historial_ventas.astype(int),
        'Total Recaudado': [f"{r:.2f} €" for r in recaudado_rama]
    })
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
