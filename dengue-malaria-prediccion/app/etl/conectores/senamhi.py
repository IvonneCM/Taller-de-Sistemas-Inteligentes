"""
Conector formal de ingesta climatica (TASK-008 / REQ-014).

Fuente ya confirmada: SENAMHI Bolivia, WIS 2.0 (ver design.md §10 y
docs/eda_inicial.md §2.2). Existia ya una descarga funcional FUERA del
backend (`scripts/descargar_senamhi.py`, de Adriana Rocha): llama a la API
OGC del WIS 2.0, filtra por estacion/variable/periodo y escribe un CSV
crudo. Esta tarea NO reemplaza ni rediseña esa logica — la adapta para que
el backend pueda formalmente ingerir su resultado hacia `datos_climaticos`.

Dos entradas soportadas, correspondientes a las dos etapas reales del
pipeline de datos del equipo:

1. `procesar_feature_api` — el mismo parseo de una "feature" cruda de la API
   OGC que usa `scripts/descargar_senamhi.py::procesar_feature`, por si en
   el futuro el backend necesita llamar la API directamente en vez de leer
   el CSV ya descargado.
2. `leer_clima_diario_csv` / `ingerir_clima_diario` — la ruta real usada hoy:
   tomar el CSV diario ya agregado por el pipeline de datos del equipo
   (`data/processed/clima_diario.csv`, con columnas
   municipio/fecha/temperatura_media/humedad_media/precipitacion_24h) y
   escribirlo en `datos_climaticos` con `fuente` poblada.

No se reemplaza el control de calidad climatico ya hecho (eso vive en
`scripts/procesar_clima.py` y `docs/reglas_calidad_datos.md`); este conector
asume que el CSV de entrada ya fue validado aguas arriba y solo se encarga
de la escritura formal en el esquema del backend.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from app.models import DatoClimatico, Municipio

FUENTE_SENAMHI = "SENAMHI Bolivia - WIS 2.0"

VARIABLES_API_VALIDAS = {
    "air_temperature",
    "relative_humidity",
    "total_precipitation_or_total_water_equivalent",
}


# ============================================================
# 1. Parseo de una feature cruda de la API OGC (adaptado de
#    scripts/descargar_senamhi.py::procesar_feature)
# ============================================================

def procesar_feature_api(feature: dict, estaciones: dict[str, str]) -> dict | None:
    """Misma logica de `scripts/descargar_senamhi.py::procesar_feature`,
    reescrita para no depender de variables globales de script: recibe el
    mapeo wigos_id -> nombre_municipio como parametro.

    Devuelve None si la feature no corresponde a una variable/estacion
    valida (igual que el script original).
    """

    propiedades = feature.get("properties", {}) or {}

    variable = propiedades.get("name")
    if variable not in VARIABLES_API_VALIDAS:
        return None

    wigos = propiedades.get("wigos_station_identifier")
    if wigos not in estaciones:
        return None

    fecha = propiedades.get("reportTime")
    if not fecha:
        return None

    try:
        fecha = pd.to_datetime(fecha)
    except Exception:
        return None

    return {
        "fecha_hora": fecha.isoformat(),
        "municipio": estaciones[wigos],
        "variable": variable,
        "valor": propiedades.get("value"),
        "unidad": propiedades.get("units"),
        "fuente": FUENTE_SENAMHI,
    }


# ============================================================
# 2. Ingesta del CSV diario ya agregado (ruta real hoy)
# ============================================================

COLUMNAS_REQUERIDAS = {"municipio", "fecha", "temperatura_media", "humedad_media", "precipitacion_24h"}


def leer_clima_diario_csv(ruta_csv: str) -> pd.DataFrame:
    """Lee el CSV diario agregado (formato de `data/processed/clima_diario.csv`)
    y valida que tenga las columnas minimas esperadas antes de ingerirlo."""

    df = pd.read_csv(ruta_csv)
    faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
    if faltantes:
        raise ValueError(
            f"El CSV de clima diario no tiene las columnas esperadas: {faltantes}"
        )

    df["municipio"] = df["municipio"].astype(str).str.strip().str.upper()
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    return df


def ingerir_clima_diario(
    db: Session, filas: pd.DataFrame | Iterable[dict], fuente: str = FUENTE_SENAMHI
) -> dict:
    """Inserta filas de clima diario en `datos_climaticos`.

    - Resuelve `municipio_id` por nombre contra el catalogo ya cargado
      (ver app/etl/seed_catalogo.py); si el municipio no existe en el
      catalogo, la fila se descarta y se cuenta en `sin_municipio` (no se
      inventa un municipio nuevo).
    - Respeta `UNIQUE(municipio_id, fecha)`: si la fila ya existe, se
      cuenta en `duplicados` y no se reinserta.
    - `es_dato_imputado` queda en False aqui: este conector escribe lo
      observado; la imputacion de huecos es responsabilidad de TASK-010
      (app/etl/limpieza.py), no de este conector.
    """

    if isinstance(filas, pd.DataFrame):
        registros = filas.to_dict(orient="records")
    else:
        registros = list(filas)

    cache_municipios: dict[str, int | None] = {}
    insertados = 0
    duplicados = 0
    sin_municipio = 0

    for fila in registros:
        nombre_municipio = str(fila["municipio"]).strip().upper()

        if nombre_municipio not in cache_municipios:
            municipio = db.query(Municipio).filter_by(nombre=nombre_municipio).first()
            cache_municipios[nombre_municipio] = municipio.id if municipio else None

        municipio_id = cache_municipios[nombre_municipio]
        if municipio_id is None:
            sin_municipio += 1
            continue

        fecha_valor = fila["fecha"]
        if isinstance(fecha_valor, str):
            fecha_valor = pd.to_datetime(fecha_valor).date()
        elif isinstance(fecha_valor, pd.Timestamp):
            fecha_valor = fecha_valor.date()

        ya_existe = (
            db.query(DatoClimatico)
            .filter_by(municipio_id=municipio_id, fecha=fecha_valor)
            .first()
        )
        if ya_existe is not None:
            duplicados += 1
            continue

        db.add(
            DatoClimatico(
                municipio_id=municipio_id,
                fecha=fecha_valor,
                temperatura_media_c=_a_numero(fila.get("temperatura_media")),
                humedad_relativa_pct=_a_numero(fila.get("humedad_media")),
                precipitacion_mm=_a_numero(fila.get("precipitacion_24h")),
                fuente=fuente,
                es_dato_imputado=False,
            )
        )
        insertados += 1

    db.flush()

    return {
        "insertados": insertados,
        "duplicados": duplicados,
        "sin_municipio": sin_municipio,
        "total_filas_recibidas": len(registros),
    }


def _a_numero(valor):
    if valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(numero) else round(numero, 1)
