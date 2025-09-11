# app.py

import pandas as pd
import networkx as nx
import streamlit as st
import matplotlib.pyplot as plt
from unidecode import unidecode

# --- Módulos de la Aplicación ---
from main import main_kpi
from main import main_comparativo
from main import heatmap_ventas
from main import kpi_engine
from main import schema_maper # O schema_mapper si lo renombras
from main.utils import normalizar_columnas

def main():
    st.set_page_config(layout="wide")

# 1) Subir archivo + elegir empresa (puede ser un selectbox o input)
empresa = st.sidebar.text_input("Empresa / Perfil", value="default")
archivo = st.sidebar.file_uploader("Sube Excel o CSV", type=["xlsx", "csv"], key="uploader_main")

if archivo:
    df_can, meta = schema_maper.run_mapping_pipeline(archivo, empresa=empresa)
    with st.expander("Diagnóstico de mapeo"):
        st.write(meta)
        st.dataframe(df_can.head())

    # 2) Calcular KPIs disponible
    results, report = kpi_engine.compute_kpis(df_can)
    st.subheader("KPIs disponibles")
    st.write(results)
    st.subheader("Estado por KPI")
    st.dataframe(report)

# Reemplaza la función completa en tu archivo app.py con esta versión final:

def detectar_y_cargar_archivo(archivo):
    xls = pd.ExcelFile(archivo)
    hojas = xls.sheet_names
    grafo = nx.Graph()

    # Primero, lee el DataFrame sin importar el caso
    if len(hojas) > 1:
        hoja_seleccionada = "X AGENTE" if "X AGENTE" in hojas else st.sidebar.selectbox("📄 Selecciona la hoja a leer", hojas)
        df = pd.read_excel(xls, sheet_name=hoja_seleccionada)
    else:
        hoja_seleccionada = hojas[0]
        preview = pd.read_excel(xls, sheet_name=hoja_seleccionada, nrows=5, header=None)
        contiene_contpaqi = preview.iloc[0, 0]
        skiprows = 3 if isinstance(contiene_contpaqi, str) and "contpaqi" in contiene_contpaqi.lower() else 0
        df = pd.read_excel(xls, sheet_name=hoja_seleccionada, skiprows=skiprows)

    # --- NORMALIZACIÓN UNIVERSAL ---
    # Ahora que tenemos el df, normalizamos las columnas SIEMPRE
    df = normalizar_columnas(df)
    st.success("✅ Columnas normalizadas correctamente.")

    # Ahora que las columnas están limpias, creamos 'año' y 'mes' si es posible
    if "fecha" in df.columns:
        try:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            # Se crea 'año' directamente para que el código posterior lo encuentre
            df["ano"] = df["fecha"].dt.year
            df["mes"] = df["fecha"].dt.month
            st.success("✅ Columnas virtuales 'año' y 'mes' generadas.")
        except Exception as e:
            st.error(f"❌ Error al procesar la columna 'fecha': {e}")
    else:
        st.warning("⚠️ No se encontró la columna 'fecha' para generar 'año' y 'mes'.")

    return df, grafo

# ETL UI (gracia si aún no lo has copiado)
try:
    from main import etl_ventas_items_ui
    HAS_ETL_UI = True
except Exception:
    HAS_ETL_UI = False

st.set_page_config(layout="wide")


# 🛠️ FUNCIÓN: Carga de Excel con detección de múltiples hojas y CONTPAQi
def detectar_y_cargar_archivo(archivo):
    xls = pd.ExcelFile(archivo)
    hojas = xls.sheet_names

    # Crear grafo para las relaciones entre las hojas
    grafo = nx.Graph()

    # Caso 1: Si hay múltiples hojas → Forzar lectura de "X AGENTE"
    if len(hojas) > 1:
        if "X AGENTE" in hojas:
            hoja = "X AGENTE"
            st.info("📌 Archivo con múltiples hojas detectado. Leyendo hoja 'X AGENTE'.")
        else:
            st.warning("⚠️ Múltiples hojas detectadas pero no se encontró la hoja 'X AGENTE'. Selecciona manualmente.")
            hoja = st.sidebar.selectbox("📄 Selecciona la hoja a leer", hojas)

        df = pd.read_excel(xls, sheet_name=hoja)

        # Generación virtual de columnas año y mes para X AGENTE
        if hoja == "X AGENTE":
            if "fecha" in df.columns:
                try:
                    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
                    df["año"] = df["fecha"].dt.year
                    df["mes"] = df["fecha"].dt.month
                    st.success("✅ Columnas virtuales 'año' y 'mes' generadas correctamente desde 'fecha' en X AGENTE.")
                except Exception as e:
                    st.error(f"❌ Error al procesar la columna 'fecha' en X AGENTE: {e}")
            else:
                st.error("❌ No existe columna 'fecha' en X AGENTE para poder generar 'año' y 'mes'.")

    else:
        # Caso 2: Solo una hoja → Detectar si es CONTPAQi
        hoja = hojas[0]
        st.info(f"✅ Solo una hoja encontrada: **{hoja}**. Procediendo con detección CONTPAQi.")
        preview = pd.read_excel(xls, sheet_name=hoja, nrows=5, header=None)
        contiene_contpaqi = preview.iloc[0, 0]
        skiprows = 3 if isinstance(contiene_contpaqi, str) and "contpaqi" in contiene_contpaqi.lower() else 0
        if skiprows:
            st.info("📌 Archivo CONTPAQi detectado. Saltando primeras 3 filas.")
        df = pd.read_excel(xls, sheet_name=hoja, skiprows=skiprows)
        df = normalizar_columnas(df)

    return df, grafo

archivo = st.sidebar.file_uploader("📂 Sube archivo de ventas (.csv o .xlsx)", type=["csv", "xlsx"])

if archivo:
    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
        df = normalizar_columnas(df)
        grafo = nx.Graph()  # Crear el grafo para CSV
    else:
        df, grafo = detectar_y_cargar_archivo(archivo)

    # Guardar archivo original para KPI CxC
    st.session_state["archivo_excel"] = archivo

    # Detectar y renombrar columna de año
    for col in df.columns:
        if col in ["ano", "anio", "año", "aÃ±o", "aã±o"]:
            df = df.rename(columns={col: "año"})
            break

    if "año" in df.columns:
        df["año"] = pd.to_numeric(df["año"], errors="coerce")

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str)

    # Detectar columna de ventas
    columnas_ventas_usd = ["valor_usd", "ventas_usd", "ventas_usd_con_iva"]
    columna_encontrada = next((col for col in columnas_ventas_usd if col in df.columns), None)

    if not columna_encontrada:
        st.warning("⚠️ No se encontró la columna 'valor_usd', 'ventas_usd' ni 'ventas_usd_con_iva'.")
        st.write("Columnas detectadas:")
        st.write(df.columns.tolist())
    else:
        st.success(f"✅ Columna de ventas detectada: **{columna_encontrada}**")
        st.session_state["columna_ventas"] = columna_encontrada

    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    st.session_state["df"] = df
    st.session_state["archivo_path"] = archivo

    if "año" in df.columns:
        with st.expander("🛠️ Diagnóstico de columnas (debug)"):
            st.write("Columnas detectadas:", df.columns.tolist())
            st.write("Valores únicos en columna 'año':", df["año"].unique())

        años_disponibles = sorted(df["año"].dropna().unique())
        año_base = st.sidebar.selectbox("📅 Selecciona el año base", años_disponibles)
        st.session_state["año_base"] = año_base
        st.success(f"📌 Año base seleccionado: {año_base}")
    else:
        st.warning("⚠️ No se encontró columna 'año' para seleccionar año base.")

# ───────────────────────────────
# Navegación
# ───────────────────────────────
menu_items = [
    "📈 KPIs Generales",
    "📊 Comparativo Año vs Año",
    "🔥 Heatmap Ventas",
    "💳 KPI Cartera CxC",
]
if HAS_ETL_UI:
    menu_items.append("🧩 Consolidación (Hoja 3)")

menu = st.sidebar.radio("Navegación", menu_items)

# Verificamos que el DataFrame exista antes de mostrar las opciones
if "df" in st.session_state:
    df_procesado = st.session_state["df"]
    año_base = st.session_state.get("año_base")

    if menu == "📈 KPIs Generales":
        main_kpi.run(df_procesado)  # <--- Le pasamos el df

    elif menu == "📊 Comparativo Año vs Año":
        main_comparativo.run(df_procesado, año_base=año_base) # <--- Le pasamos el df

    elif menu == "🔥 Heatmap Ventas":
        heatmap_ventas.run(df_procesado) # <--- Le pasamos el df

    elif menu == "💳 KPI Cartera CxC":
        kpi_cpc.run(st.session_state["archivo_excel"]) # Este se queda igual, ya recibe el archivo

    elif menu == "🧩 Consolidación (Hoja 3)" and HAS_ETL_UI:
        etl_ventas_items_ui.run()

elif archivo:
    # Si el archivo se acaba de cargar, pide recargar
    st.info("Archivo procesado. Por favor selecciona una opción del menú de navegación.")

else:
    st.info("Bienvenido. Por favor, sube un archivo en el menú lateral para comenzar.")

# Al final del archivo, añade estas dos líneas:
if __name__ == "__main__":
    main()
