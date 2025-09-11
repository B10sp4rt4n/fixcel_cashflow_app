
import pandas as pd

def calcular_flujo_caja(datos):
    """Calcula el flujo de caja basándose en los datos históricos de entradas y salidas."""
    entradas = datos["entradas"]
    salidas = datos["salidas"]
    flujo_neto = sum(entradas) - sum(salidas)

    return flujo_neto

def proyeccion_flujo(datos, meses=3):
    """Realiza una proyección del flujo de caja utilizando los datos históricos."""
    # Usando una proyección simple de promedio
    entradas_promedio = sum(datos["entradas"]) / len(datos["entradas"])
    salidas_promedio = sum(datos["salidas"]) / len(datos["salidas"])

    # Proyección para los próximos meses
    proyeccion = {
        "entradas": [entradas_promedio * (meses + i) for i in range(1, meses+1)],
        "salidas": [salidas_promedio * (meses + i) for i in range(1, meses+1)]
    }

    return proyeccion
