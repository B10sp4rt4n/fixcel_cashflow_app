# main/schema_mapper.py
from __future__ import annotations
import os
from typing import Dict, List, Tuple, Optional
import pandas as pd
from unidecode import unidecode

# ---- Fuzzy (opcional) --------------------------------------------------------
try:
    from rapidfuzz import process, fuzz
    HAS_FUZZ = True
except Exception:
    HAS_FUZZ = False

# ---- YAML config -------------------------------------------------------------
try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False

# =============================================================================
# 1) Normalización y utilidades
# =============================================================================
def normalize_header(name: str) -> str:
    s = unidecode(str(name)).strip().lower()
    s = s.replace(".", " ").replace("-", " ").replace("/", " ")
    s = "_".join(s.split())
    return s

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_header(c) for c in df.columns]
    return df

def parse_fecha_y_derivar(df: pd.DataFrame, fecha_col: str = "fecha") -> pd.DataFrame:
    df = df.copy()
    if fecha_col in df.columns:
        df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
        if "año" not in df.columns:
            df["año"] = df[fecha_col].dt.year
        if "mes" not in df.columns:
            df["mes"] = df[fecha_col].dt.month
    return df

# =============================================================================
# 2) Carga de perfil (empresa) y esquema
# =============================================================================
DEFAULT_CANONICAL = [
    "fecha", "año", "mes", "cliente_id", "cliente_nombre",
    "agente", "producto", "cantidad", "importe", "moneda"
]

DEFAULT_SYNONYMS = {
    "fecha": ["fecha", "date", "f_emision", "periodo"],
    "año": ["ano", "anio", "año", "year"],
    "mes": ["mes", "month"],
    "cliente_id": ["cliente", "id_cliente", "customer_id", "id"],
    "cliente_nombre": ["cliente_nombre", "razon_social", "customer_name", "cliente_desc"],
    "agente": ["agente", "agent", "vendedor", "seller"],
    "producto": ["producto", "item", "sku", "articulo"],
    "cantidad": ["cantidad", "qty", "unidades", "uds"],
    "importe": ["importe", "valor_usd", "ventas_usd", "monto", "total", "subtotal", "sales"],
    "moneda": ["moneda", "currency", "divisa"]
}

def _configs_dir() -> str:
    return os.path.join(os.getcwd(), "configs")

def load_profile(empresa: str) -> Dict:
    """
    Carga configs/{empresa}.yaml; si no existe, intenta configs/default.yaml;
    si no hay YAML, devuelve un perfil mínimo en memoria.
    """
    cfg_dir = _configs_dir()
    paths = [
        os.path.join(cfg_dir, f"{empresa}.yaml"),
        os.path.join(cfg_dir, "default.yaml"),
    ]
    if HAS_YAML:
        for p in paths:
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
    # Fallback mínimo
    return {
        "sheet": "X AGENTE",
        "skiprows": 0,
        "columns": {},         # mapeos específicos empresa -> canónicos
        "synonyms": DEFAULT_SYNONYMS,
        "canonical": DEFAULT_CANONICAL,
        "rules": {}
    }

# =============================================================================
# 3) Detección de hoja y lectura
# =============================================================================
def pick_sheet(xls: pd.ExcelFile, preferred: Optional[str] = "X AGENTE") -> str:
    if preferred and preferred in xls.sheet_names:
        return preferred
    # fallback: primera hoja
    return xls.sheet_names[0]

def read_any(archivo, sheet: Optional[str] = None, skiprows: int = 0) -> pd.DataFrame:
    name = getattr(archivo, "name", str(archivo))
    if name.lower().endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        xls = pd.ExcelFile(archivo)
        hoja = sheet or pick_sheet(xls, preferred="X AGENTE")
        df = pd.read_excel(xls, sheet_name=hoja, skiprows=skiprows)
    return df

# =============================================================================
# 4) Auto mapeo de columnas a canónicas
# =============================================================================
def automap_columns(
    df: pd.DataFrame,
    canonical: List[str],
    synonyms: Dict[str, List[str]],
    threshold: int = 86
) -> Dict[str, Optional[str]]:
    """
    Devuelve dict: {canonico: columna_origen (o None)}.
    Prioriza coincidencia exacta de encabezados normalizados,
    luego sinónimos, y opcionalmente fuzzy.
    """
    df_norm_cols = [normalize_header(c) for c in df.columns]
    mapping: Dict[str, Optional[str]] = {k: None for k in canonical}

    # 1) exact match por nombre normalizado
    for can in canonical:
        if can in df_norm_cols:
            idx = df_norm_cols.index(can)
            mapping[can] = df.columns[idx]

    # 2) sinónimos si no fue cubierto
    for can, syns in synonyms.items():
        if mapping.get(can):
            continue
        # buscar primer sinónimo que exista
        for s in syns:
            s_norm = normalize_header(s)
            if s_norm in df_norm_cols:
                idx = df_norm_cols.index(s_norm)
                mapping[can] = df.columns[idx]
                break

    # 3) fuzzy (opcional)
    if HAS_FUZZ:
        for can in canonical:
            if mapping.get(can):
                continue
            candidates = process.extract(
                can, df_norm_cols, scorer=fuzz.token_sort_ratio, limit=3
            )
            if candidates:
                best, score, idx = candidates[0]
                if score >= threshold:
                    mapping[can] = df.columns[idx]

    return mapping

def apply_mapping(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """
    Renombra columnas de origen al nombre canónico cuando haya match.
    """
    df = df.copy()
    rename_map = {src: can for can, src in mapping.items() if src}
    df = df.rename(columns=rename_map)
    return df

# =============================================================================
# 5) Validaciones y pipeline
# =============================================================================
def validate_minimum(df: pd.DataFrame, minimum_fields: List[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in minimum_fields if c not in df.columns]
    return (len(missing) == 0, missing)

def run_mapping_pipeline(
    archivo,
    empresa: str,
    minimum_fields: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Lee el archivo, aplica perfil (hoja/skiprows), normaliza, auto-mapea,
    deriva año/mes si hay fecha, y valida mínimos.
    """
    profile = load_profile(empresa)
    sheet = profile.get("sheet")
    skiprows = int(profile.get("skiprows", 0))
    synonyms = profile.get("synonyms") or DEFAULT_SYNONYMS
    canonical = profile.get("canonical") or DEFAULT_CANONICAL
    explicit_map = profile.get("columns") or {}

    raw_df = read_any(archivo, sheet=sheet, skiprows=skiprows)
    norm_df = normalize_columns(raw_df)

    # Auto-mapeo + overrides del perfil (columns)
    auto_map = automap_columns(norm_df, canonical, synonyms)
    # Si el perfil indica una columna específica para algún canónico, pisa el automap
    for can, src in explicit_map.items():
        if src in raw_df.columns:
            auto_map[can] = src

    mapped_df = apply_mapping(norm_df, auto_map)
    mapped_df = parse_fecha_y_derivar(mapped_df, fecha_col="fecha")

    # Validación mínima (por defecto: fecha + importe)
    minimum_fields = minimum_fields or ["fecha", "importe"]
    ok, missing = validate_minimum(mapped_df, minimum_fields)

    meta = {
        "empresa": empresa,
        "sheet_used": sheet,
        "skiprows_used": skiprows,
        "auto_map": auto_map,
        "ok_minimum": ok,
        "missing_minimum": missing,
    }
    return mapped_df, meta
