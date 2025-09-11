# Contenido completo para main/utils.py
from unidecode import unidecode

def normalizar_columnas(df):
    nuevas_columnas = []
    for col in df.columns:
        col_str = str(col).lower().strip().replace(" ", "_")
        col_str = unidecode(col_str)
        nuevas_columnas.append(col_str)
    df.columns = nuevas_columnas
    return df