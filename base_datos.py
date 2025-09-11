
import sqlite3
import pandas as pd

def cargar_datos_iniciales(df):
    """Carga los datos históricos iniciales en la base de datos."""
    conn = sqlite3.connect('fixcel_cashflow.db')
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flujo_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT,
            entradas REAL,
            salidas REAL
        )
    ''')

    # Insertar los datos en la tabla
    for index, row in df.iterrows():
        cursor.execute("INSERT INTO flujo_caja (mes, entradas, salidas) VALUES (?, ?, ?)",
                       (row['mes'], row['entradas'], row['salidas']))

    conn.commit()
    conn.close()
    print("Datos iniciales cargados con éxito.")

def cargar_datos_incrementales(df):
    """Carga nuevos datos (incrementales) en la base de datos sin duplicar registros existentes."""
    conn = sqlite3.connect('fixcel_cashflow.db')
    cursor = conn.cursor()

    # Verificar si la base de datos ya tiene registros del mismo mes
    for index, row in df.iterrows():
        cursor.execute("SELECT * FROM flujo_caja WHERE mes = ?", (row['mes'],))
        data_existente = cursor.fetchone()

        if data_existente:
            # Si el mes ya existe, actualizar el registro
            cursor.execute("UPDATE flujo_caja SET entradas = ?, salidas = ? WHERE mes = ?",
                           (row['entradas'], row['salidas'], row['mes']))
        else:
            # Si el mes no existe, insertar el nuevo registro
            cursor.execute("INSERT INTO flujo_caja (mes, entradas, salidas) VALUES (?, ?, ?)",
                           (row['mes'], row['entradas'], row['salidas']))

    conn.commit()
    conn.close()
    print("Datos incrementales cargados con éxito.")

def obtener_datos_historial():
    """Obtiene los datos históricos de la base de datos."""
    conn = sqlite3.connect('fixcel_cashflow.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flujo_caja")
    datos = cursor.fetchall()
    conn.close()

    # Formatear los datos para Streamlit
    return pd.DataFrame(datos, columns=["mes", "entradas", "salidas"])
