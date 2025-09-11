
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from flujo_caja import calcular_flujo_caja, proyeccion_flujo
from base_datos import cargar_datos_iniciales, cargar_datos_incrementales, obtener_datos_historial
from relaciones import verificar_relaciones, mostrar_alertas

import pandas as pd
import streamlit as st

# Cargar el archivo
archivo_inicial = st.file_uploader("Cargar archivo completo de datos")

if archivo_inicial is not None:
    # Cargar los datos en un DataFrame
    df_inicial = pd.read_excel(archivo_inicial)  # O pd.read_csv(archivo_inicial) si es CSV
    
    # Verificar las columnas del DataFrame
    st.write("Columnas del archivo cargado:", df_inicial.columns)
    
    # Mostrar las primeras filas para ver el contenido
    st.write("Primeras filas del archivo cargado:", df_inicial.head())
    
    # Verificar si la columna 'mes' está presente
    if 'mes' not in df_inicial.columns:
        st.error("La columna 'mes' no está presente en el archivo.")
    else:
        st.success("La columna 'mes' está presente en el archivo.")
        
    # Si el nombre de la columna es diferente, renombrarla
    if 'Nombre_original_de_mes' in df_inicial.columns:
        df_inicial.rename(columns={'Nombre_original_de_mes': 'mes'}, inplace=True)
        st.write("Columna renombrada a 'mes'.")

    # Procesar los datos según sea necesario
    cargar_datos_iniciales(df_inicial)
    st.success("Datos cargados exitosamente.")


st.set_page_config(page_title="FixCel - Dashboard de Flujo de Caja", layout="wide")
st.title("📊 FixCel - Dashboard de Flujo de Caja y Relaciones")

# Menú de navegación
menu = st.sidebar.radio("Navegar", [
    "Carga de Datos Iniciales",
    "Carga de Datos Incrementales",
    "Análisis de Flujo de Caja",
    "Proyecciones de Flujo de Caja",
    "Verificación de Relaciones"
])

# Cargar datos iniciales
if menu == "Carga de Datos Iniciales":
    st.header("📥 Cargar Datos Iniciales")
    archivo_inicial = st.file_uploader("Cargar archivo completo de datos históricos (Excel o CSV)", type=["xlsx", "csv"])

    if archivo_inicial is not None:
        df_inicial = pd.read_excel(archivo_inicial)  # O pd.read_csv(archivo_inicial) si es CSV
        st.write("Vista previa de los datos cargados:")
        st.dataframe(df_inicial)

        # Cargar los datos en la base de datos
        cargar_datos_iniciales(df_inicial)
        st.success("Datos históricos cargados exitosamente.")

# Cargar datos incrementales
elif menu == "Carga de Datos Incrementales":
    st.header("📥 Cargar Datos Incrementales")
    archivo_incremental = st.file_uploader("Cargar archivo de datos incrementales (Excel o CSV)", type=["xlsx", "csv"])

    if archivo_incremental is not None:
        df_incremental = pd.read_excel(archivo_incremental)  # O pd.read_csv(archivo_incremental) si es CSV
        st.write("Vista previa de los datos incrementales cargados:")
        st.dataframe(df_incremental)

        # Cargar los datos incrementales en la base de datos
        cargar_datos_incrementales(df_incremental)
        st.success("Datos incrementales cargados exitosamente.")

# Análisis de Flujo de Caja
elif menu == "Análisis de Flujo de Caja":
    st.header("💸 Análisis de Flujo de Caja")
    datos_historial = obtener_datos_historial()
    if not datos_historial.empty:
        flujo_caja = calcular_flujo_caja(datos_historial)
        st.write(f"Flujo de Caja Neto: ${flujo_caja}")

        # Visualización del flujo de caja
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(datos_historial["mes"], datos_historial["entradas"], label="Entradas", color="green")
        ax.plot(datos_historial["mes"], datos_historial["salidas"], label="Salidas", color="red")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Monto ($)")
        ax.set_title("Flujo de Caja")
        ax.legend()
        st.pyplot(fig)
    else:
        st.warning("No hay datos históricos disponibles. Carga datos iniciales primero.")

# Proyecciones de Flujo de Caja
elif menu == "Proyecciones de Flujo de Caja":
    st.header("📈 Proyección de Flujo de Caja")
    datos_historial = obtener_datos_historial()

    if not datos_historial.empty:
        proyeccion = proyeccion_flujo(datos_historial)

        # Mostrar proyecciones para los próximos meses
        st.write("Proyección de Flujo de Caja para los próximos 3 meses:")
        st.write(proyeccion)

        # Visualizar las proyecciones
        meses = ['Mes 1', 'Mes 2', 'Mes 3']
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(meses, proyeccion["entradas"], label="Proyección Entradas", color="blue")
        ax.plot(meses, proyeccion["salidas"], label="Proyección Salidas", color="orange")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Monto ($)")
        ax.set_title("Proyección de Flujo de Caja")
        ax.legend()
        st.pyplot(fig)
    else:
        st.warning("No hay datos históricos disponibles para realizar la proyección.")

# Verificación de Relaciones
elif menu == "Verificación de Relaciones":
    st.header("🔍 Verificación de Relaciones entre Hojas")
    grafo = verificar_relaciones()

    if grafo:
        st.success("Las relaciones entre hojas están intactas.")
    else:
        st.warning("Existen relaciones rotas entre las hojas. Por favor, revisa los datos.")
