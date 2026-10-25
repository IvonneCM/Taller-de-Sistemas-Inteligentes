"""
Conector formal de ingesta epidemiologica (TASK-009 / REQ-014).

Fuente ya confirmada: Ministerio de Salud y Deportes de Bolivia, Boletin
Epidemiologico N.13 (2026) (ver design.md §10, docs/eda_inicial.md §2.1).

LIMITACION DE GRANULARIDAD (decision registrada el 2026-10-25, ver
CONTEXT.md y docs/resultados_linea_base.md, Experimentos C y D):
la fuente entrega UN SOLO acumulado por municipio para todo el periodo
SE1-13, no una serie semana a semana. El propio Experimento D del equipo
("protocolo_baseline.json") deja constancia de que el requisito minimo para
un modelo municipio-semana "hoy no existe (solo acumulados SE1-13)", y el
Experimento C muestra con numeros por que forzar ese nivel de detalle con
los datos actuales produce sobreajuste (R²=1.0 con 0 grados de libertad).

Por eso este conector NO fabrica una serie semanal: inserta exactamente lo
que la fuente reporta, un registro por (municipio, enfermedad, periodo
acumulado). `fecha_reporte` se fija al ULTIMO DIA del periodo acumulado
(domingo de la semana epidemiologica de cierre, ej. SE13 de 2026) como
fecha representativa del cierre del periodo, no como un conteo diario o
semanal real — se documenta explicitamente para que nadie la interprete mal
en TASK-011 (features) o TASK-014 (prediccion).

Entrada esperada: los CSV ya validados por el pipeline de Linea Base
(Paso 2, `scripts/limpieza_datos.py`): `dengue_municipal_validado.csv` y
`malaria_municipal_validado.csv` (en `data/processed/`). Ese pipeline ya
aplico las reglas COM-xx/EPI-xx; este conector solo re-valida que no haya
columnas de PII (defensa en profundidad, REQ-020) e ingiere las filas con
`estado_calidad == 'valido'`.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models import CasoEpidemiologico, Enfermedad, Municipio

FUENTE_MINSALUD = "Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13"

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
