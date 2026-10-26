"""
Conector formal de ingesta epidemiologica (TASK-009 / REQ-014).

Fuente ya confirmada: Ministerio de Salud y Deportes de Bolivia, Boletin
Epidemiologico N.13 (2026) (ver design.md §10, docs/eda_inicial.md §2.1).

GRANULARIDAD (decision 2 del reparto "Listo para Empezar", 2026-10-25):
  - DENGUE: serie semanal real por municipio (SE1-13), extraida del mismo
    Boletin N.13 por `scripts/extraer_dengue_semanal.py` y verificada contra
    los totales impresos. Se ingiere con `ingerir_dengue_semanal`: una fila
    por (municipio, semana), con `fecha_reporte` = domingo de esa semana ISO.
  - MALARIA: NO existe serie semanal en ninguna fuente disponible; solo
    acumulados SE1-k por boletin. Se ingiere con
    `ingerir_epidemiologia_acumulada`: una fila por municipio con el
    acumulado SE1-13 y `fecha_reporte` = cierre del periodo (no un conteo
    semanal). Los bloques reconstruidos por diferencia entre boletines
    (data/processed/malaria_municipal_bloques.csv) NO se ingieren aqui:
    ver la nota sobre el esquema en docs/guia_entrega_fase2.md.

No mezclar las dos formas para la MISMA enfermedad: sumar un acumulado SE1-13
y las 13 filas semanales de dengue duplicaria los casos. Por eso
`ingerir_epidemiologia_acumulada("dengue")` emite una advertencia y las filas
semanales usan una `fuente` distinta (FUENTE_MINSALUD_SEMANAL).

Entrada esperada: los CSV ya validados por el pipeline de Linea Base
(Paso 2, `scripts/limpieza_datos.py`): `dengue_municipal_validado.csv` y
`malaria_municipal_validado.csv` (en `data/processed/`). Ese pipeline ya
aplico las reglas COM-xx/EPI-xx; este conector solo re-valida que no haya
columnas de PII (defensa en profundidad, REQ-020) e ingiere las filas con
`estado_calidad == 'valido'`.
"""

from __future__ import annotations

import warnings
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models import CasoEpidemiologico, Enfermedad, Municipio

FUENTE_MINSALUD = "Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13"
# `casos_epidemiologicos.fuente` es VARCHAR(100): este texto debe medir <= 100.
FUENTE_MINSALUD_SEMANAL = "Min. Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13 (serie semanal)"

# Columnas que NUNCA deben aparecer en un dataset epidemiologico (REQ-020).
# Defensa en profundidad: el pipeline de Linea Base (Paso 2) ya valida esto
# (ver scripts/limpieza_datos.py::validar_sin_pii); este conector repite el
# chequeo antes de escribir en la base de datos del backend.
COLUMNAS_PII_PROHIBIDAS = {
    "nombre", "apellido", "ci", "carnet", "documento", "direccion",
    "telefono", "paciente", "historia_clinica",
}

# Mapeo por enfermedad: nombre de la columna de casos en el CSV validado.
COLUMNA_CASOS_POR_ENFERMEDAD = {
    "dengue": "casos_dengue_acumulados_se1_13",
    "malaria": "total_malaria",
}


def _validar_sin_pii(df: pd.DataFrame, nombre_dataset: str) -> None:
    columnas = {c.lower() for c in df.columns}
    interseccion = columnas & COLUMNAS_PII_PROHIBIDAS
    if interseccion:
        raise ValueError(
            f"REQ-020: {nombre_dataset} contiene columnas con posibles datos "
            f"personales de pacientes: {interseccion}. El conector se detiene."
        )


def fecha_cierre_periodo(anio: int, semana_epidemiologica_cierre: int = 13) -> date:
    """Domingo de la semana ISO `semana_epidemiologica_cierre` del `anio`
    dado — fecha representativa del cierre de un periodo acumulado SE1-N.
    NO representa un reporte diario ni semanal real (ver limitacion arriba).
    """
    lunes = date.fromisocalendar(anio, semana_epidemiologica_cierre, 1)
    return date.fromordinal(lunes.toordinal() + 6)


def leer_epidemiologia_municipal_csv(ruta_csv: str, enfermedad: str) -> pd.DataFrame:
    if enfermedad not in COLUMNA_CASOS_POR_ENFERMEDAD:
        raise ValueError(f"Enfermedad no reconocida: {enfermedad}")

    df = pd.read_csv(ruta_csv)
    _validar_sin_pii(df, ruta_csv)

    columnas_requeridas = {"municipio", "anio", "estado_calidad", COLUMNA_CASOS_POR_ENFERMEDAD[enfermedad]}
    faltantes = columnas_requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta_csv} no tiene las columnas esperadas: {faltantes}")

    df["municipio"] = df["municipio"].astype(str).str.strip().str.upper()
    return df


def fecha_fin_semana(anio: int, semana_epidemiologica: int) -> date:
    """Domingo de la semana ISO dada: `fecha_reporte` de una fila SEMANAL.
    Usa la misma convencion ISO (lunes-domingo) que el clima del pipeline de
    datos (scripts/procesar_clima.py), para que ambas fuentes crucen por fecha.
    """
    lunes = date.fromisocalendar(anio, semana_epidemiologica, 1)
    return date.fromordinal(lunes.toordinal() + 6)


def leer_dengue_semanal_csv(ruta_csv: str) -> pd.DataFrame:
    """Lee `dengue_municipal_semanal.csv` (formato largo: una fila por
    municipio-semana) y lo valida antes de tocar la base de datos."""
    df = pd.read_csv(ruta_csv)
    _validar_sin_pii(df, ruta_csv)

    requeridas = {"municipio", "anio", "semana_epidemiologica", "casos_dengue"}
    faltantes = requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta_csv} no tiene las columnas esperadas: {faltantes}")

    if df["casos_dengue"].isna().any() or (df["casos_dengue"] < 0).any():
        raise ValueError(f"{ruta_csv}: casos_dengue vacio o negativo (REQ-013).")
    if not df["semana_epidemiologica"].between(1, 53).all():
        raise ValueError(f"{ruta_csv}: semana_epidemiologica fuera de 1-53.")

    df["municipio"] = df["municipio"].astype(str).str.strip().str.upper()
    return df


def ingerir_dengue_semanal(
    db: Session,
    df: pd.DataFrame,
    fuente: str = FUENTE_MINSALUD_SEMANAL,
) -> dict:
    """Inserta la serie SEMANAL de dengue (TASK-009, decision 2 del reparto):
    una fila de `casos_epidemiologicos` por (municipio, semana).

    - `fecha_reporte` = domingo de la semana ISO; `es_dato_imputado = False`
      porque son conteos reales del boletin (nada estimado).
    - Municipios fuera del catalogo (hoy solo la zona piloto, ver
      app/etl/seed_catalogo.py) se cuentan en `sin_municipio` y se
      descartan: nunca se crean municipios al vuelo.
    - Idempotente: una segunda corrida no duplica (`duplicados`).
    """
    enfermedad_row = db.query(Enfermedad).filter_by(nombre="dengue").first()
    if enfermedad_row is None:
        raise ValueError(
            "La enfermedad 'dengue' no existe en el catalogo "
            "(app/etl/seed_catalogo.py). Cargar el catalogo antes de ingerir."
        )

    cache_municipios: dict[str, int | None] = {}
    insertados = duplicados = sin_municipio = 0

    for _, fila in df.iterrows():
        nombre = str(fila["municipio"]).strip().upper()
        if nombre not in cache_municipios:
            m = db.query(Municipio).filter_by(nombre=nombre).first()
            cache_municipios[nombre] = m.id if m else None
        municipio_id = cache_municipios[nombre]
        if municipio_id is None:
            sin_municipio += 1
            continue

        fecha_reporte = fecha_fin_semana(int(fila["anio"]), int(fila["semana_epidemiologica"]))
        ya_existe = (
            db.query(CasoEpidemiologico)
            .filter_by(
                municipio_id=municipio_id,
                enfermedad_id=enfermedad_row.id,
                fecha_reporte=fecha_reporte,
                fuente=fuente,
            )
            .first()
        )
        if ya_existe is not None:
            duplicados += 1
            continue

        db.add(
            CasoEpidemiologico(
                municipio_id=municipio_id,
                enfermedad_id=enfermedad_row.id,
                fecha_reporte=fecha_reporte,
                casos_confirmados=int(fila["casos_dengue"]),
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
        "total_filas_recibidas": len(df),
    }


def ingerir_epidemiologia_acumulada(
    db: Session,
    df: pd.DataFrame,
    enfermedad: str,
    fuente: str = FUENTE_MINSALUD,
) -> dict:
    """Inserta en `casos_epidemiologicos` las filas con
    `estado_calidad == 'valido'`, una por municipio, representando el
    acumulado SE1-13 (no una serie semanal — ver limitacion en el docstring
    del modulo).

    Igual que el conector climatico (TASK-008): si el municipio no esta en
    el catalogo (`app/etl/seed_catalogo.py`), la fila se cuenta en
    `sin_municipio` y se descarta, en vez de inventarlo.
    """

    if enfermedad == "dengue":
        warnings.warn(
            "Dengue ya tiene serie semanal: use ingerir_dengue_semanal. "
            "Ingerir tambien el acumulado SE1-13 duplicaria los casos al "
            "sumar por municipio.",
            DeprecationWarning,
            stacklevel=2,
        )

    columna_casos = COLUMNA_CASOS_POR_ENFERMEDAD[enfermedad]

    enfermedad_row = db.query(Enfermedad).filter_by(nombre=enfermedad).first()
    if enfermedad_row is None:
        raise ValueError(
            f"La enfermedad '{enfermedad}' no existe en el catalogo "
            "(app/etl/seed_catalogo.py). Cargar el catalogo antes de ingerir."
        )

    cache_municipios: dict[str, int | None] = {}
    insertados = 0
    duplicados = 0
    sin_municipio = 0
    rechazados_por_fuente = 0

    for _, fila in df.iterrows():
        if str(fila.get("estado_calidad", "")).strip().lower() != "valido":
            rechazados_por_fuente += 1
            continue

        nombre_municipio = str(fila["municipio"]).strip().upper()
        if nombre_municipio not in cache_municipios:
            municipio = db.query(Municipio).filter_by(nombre=nombre_municipio).first()
            cache_municipios[nombre_municipio] = municipio.id if municipio else None

        municipio_id = cache_municipios[nombre_municipio]
        if municipio_id is None:
            sin_municipio += 1
            continue

        anio = int(fila["anio"])
        fecha_reporte = fecha_cierre_periodo(anio)

        casos = fila[columna_casos]
        if pd.isna(casos):
            continue
        casos = int(casos)

        ya_existe = (
            db.query(CasoEpidemiologico)
            .filter_by(
                municipio_id=municipio_id,
                enfermedad_id=enfermedad_row.id,
                fecha_reporte=fecha_reporte,
                fuente=fuente,
            )
            .first()
        )
        if ya_existe is not None:
            duplicados += 1
            continue

        db.add(
            CasoEpidemiologico(
                municipio_id=municipio_id,
                enfermedad_id=enfermedad_row.id,
                fecha_reporte=fecha_reporte,
                casos_confirmados=casos,
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
        "rechazados_por_fuente": rechazados_por_fuente,
        "total_filas_recibidas": len(df),
    }
