# main/kpi_engine.py
from __future__ import annotations
from typing import Dict, List, Tuple, Any
import pandas as pd

# Catálogo de KPIs (nombre -> requisitos y función)

KPI_REGISTRY: Dict[str, Dict[str, Any]] = {}

def kpi(name: str, requires: List[str]):
    def deco(func):
        KPI_REGISTRY[name] = {"requires": requires, "fn": func}
        return func
    return deco

# ------------------- KPIs básicos --------------------------------------------
@kpi("ventas_netas", requires=["importe"])
def compute_ventas_netas(df: pd.DataFrame) -> float:
    return float(pd.to_numeric(df["importe"], errors="coerce").fillna(0).sum())

@kpi("kpi_cpc", requires=["cliente_id", "importe"])
def compute_kpi_cpc(df: pd.DataFrame) -> float:
    # Implementación del KPI aquí
    return float(df["importe"].sum())

@kpi("clientes_activos", requires=["cliente_id", "importe"])
def compute_clientes_activos(df: pd.DataFrame) -> int:
    df2 = df[pd.to_numeric(df["importe"], errors="coerce").fillna(0) > 0]
    return int(df2["cliente_id"].nunique())

@kpi("ticket_promedio", requires=["importe", "cliente_id"])
def compute_ticket_promedio(df: pd.DataFrame) -> float:
    ventas = pd.to_numeric(df["importe"], errors="coerce").fillna(0).sum()
    clientes = df["cliente_id"].nunique()
    return float(ventas / clientes) if clientes else float("nan")

@kpi("margen_bruto", requires=["importe", "cantidad", "costo_unitario"])
def compute_margen_bruto(df: pd.DataFrame) -> float:
    imp = pd.to_numeric(df["importe"], errors="coerce").fillna(0)
    cant = pd.to_numeric(df.get("cantidad"), errors="coerce").fillna(0)
    costo_u = pd.to_numeric(df.get("costo_unitario"), errors="coerce").fillna(0)
    costo_total = (cant * costo_u).fillna(0).sum()
    return float(imp.sum() - costo_total)

# ------------------- Motor ----------------------------------------------------
def check_requirements(df: pd.DataFrame, requires: List[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in requires if c not in df.columns]
    return (len(missing) == 0, missing)

def compute_kpis(
    df: pd.DataFrame,
    requested: List[str] | None = None
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Devuelve:
      - results: dict KPI -> valor (o None si no calculable)
      - report: DataFrame con estado por KPI (OK/NO), faltantes y comentario
    """
    kpis = requested or list(KPI_REGISTRY.keys())
    rows = []
    results: Dict[str, Any] = {}

    for k in kpis:
        spec = KPI_REGISTRY.get(k)
        if not spec:
            rows.append({"kpi": k, "status": "NA", "faltan": "-", "comentario": "No registrado"})
            results[k] = None
            continue

        ok, missing = check_requirements(df, spec["requires"])
        if ok:
            try:
                results[k] = spec["fn"](df)
                rows.append({"kpi": k, "status": "OK", "faltan": "", "comentario": ""})
            except Exception as e:
                results[k] = None
                rows.append({"kpi": k, "status": "ERR", "faltan": "", "comentario": str(e)})
        else:
            results[k] = None
            rows.append({
                "kpi": k,
                "status": "NO",
                "faltan": ", ".join(missing),
                "comentario": _suggest_for_missing(k, missing)
            })

    report = pd.DataFrame(rows, columns=["kpi", "status", "faltan", "comentario"])
    return results, report

def _suggest_for_missing(kpi_name: str, missing: List[str]) -> str:
    # Mensajes simples y claros
    tips = {
        "margen_bruto": "Agrega 'cantidad' y 'costo_unitario' (o provee una lista de costos).",
        "ticket_promedio": "Se requiere 'cliente_id' para contar clientes únicos.",
    }
    base = tips.get(kpi_name, "")
    if not base:
        return f"Faltan: {', '.join(missing)}"
    return f"{base} Faltan: {', '.join(missing)}"
