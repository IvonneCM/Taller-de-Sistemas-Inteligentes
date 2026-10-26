"""TASK-011 / REQ-002: features semanales sin escrituras ni acceso a BD.

Reutiliza el criterio de agrupación, rezagos y ventanas de
scripts/construir_panel_semanal.py, pero consulta semanas de calendario,
no posiciones de filas. Los huecos permanecen desconocidos (NaN).

Por defecto las medias usan exclusivamente semanas anteriores. Activar
incluir_semana_actual solo al cierre de esa semana, cuando sus datos ya
estén disponibles. Los datos retrospectivos revisados no equivalen a los
datos disponibles en tiempo real; este módulo no corrige retrasos de reporte.

Malaria por bloques no es una serie semanal: se rechaza sin repartir ni
inventar registros. La correspondencia ISO/semana epidemiológica debe
validarse en la fuente; el panel actual utiliza semanas ISO.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


DATASET_DENGUE = (
    Path(__file__).resolve().parents[3]
    / "data/processed/panel_semanal_dengue_clima.csv"
)
VARIABLES = (
    "casos_dengue", "casos_confirmados", "temperatura_media",
    "humedad_media", "precipitacion_total_mm",
)
OBJETIVOS = (
    "casos_dengue_t_mas_3", "casos_dengue_t_mas_4", "hay_casos_t_mas_3",
)
CLAVES = ["municipio", "enfermedad", "anio", "semana_epidemiologica", "fecha_semana"]


@dataclass
class ResultadoFeatures:
    """Tablas alineadas por índice; claves son metadatos, no predictores.

features contiene únicamente predictores numéricos generados aquí.
objetivos preserva los objetivos existentes, sin calcular ni imputar futuro.
continuidad indica si las cuatro semanas anteriores tienen registro,
independientemente de que sus variables tengan valores faltantes.
"""

    claves: pd.DataFrame
    features: pd.DataFrame
    objetivos: pd.DataFrame
    continuidad: pd.Series


def generar_features(
    datos: pd.DataFrame, *, incluir_semana_actual: bool = False
) -> ResultadoFeatures:
    """Genera lags 2/3/4 y medias 2/3/4 por municipio y enfermedad.

Las ventanas son completas: una semana o valor ausente deja NaN. No se
emiten filas nuevas. Se rechazan claves duplicadas, semanas ISO inválidas,
identificadores vacíos y entradas por bloques. Sin columna enfermedad solo
se admite inferir dengue cuando existe casos_dengue.
"""
    if datos.empty:
        raise ValueError("El dataset semanal está vacío; no se pueden generar features.")
    if {"se_inicio", "se_fin", "n_semanas"}.intersection(datos.columns):
        raise ValueError("Los bloques de malaria no tienen granularidad semanal.")
    requeridas = {"municipio", "anio", "semana_epidemiologica"}
    if not requeridas.issubset(datos.columns):
        raise ValueError(f"Faltan columnas: {sorted(requeridas - set(datos.columns))}")
    df = datos.copy(deep=True)
    if "enfermedad" not in df:
        if "casos_dengue" not in df:
            raise ValueError("Se requiere enfermedad; solo se puede inferir dengue.")
        df["enfermedad"] = "dengue"
    for columna in ("municipio", "enfermedad"):
        if df[columna].isna().any() or df[columna].astype(str).str.strip().eq("").any():
            raise ValueError(f"Identificador vacío: {columna}")
        df[columna] = df[columna].astype(str).str.strip().str.casefold()
    for columna in ("anio", "semana_epidemiologica"):
        numeros = pd.to_numeric(df[columna], errors="raise")
        if numeros.isna().any() or not numeros.mod(1).eq(0).all():
            raise ValueError(f"{columna} debe contener enteros sin faltantes.")
        df[columna] = numeros.astype(int)
    try:
        df["fecha_semana"] = pd.to_datetime([
            date.fromisocalendar(a, s, 1)
            for a, s in zip(df["anio"], df["semana_epidemiologica"])
        ])
    except (ValueError, OverflowError) as exc:
        raise ValueError("Año o semana ISO inválidos.") from exc
    if df.duplicated(["municipio", "enfermedad", "fecha_semana"]).any():
        raise ValueError("Claves municipio/enfermedad/semana duplicadas.")
    variables = [v for v in VARIABLES if v in df]
    if not variables:
        raise ValueError("No hay variables disponibles para generar features.")
    for variable in variables:
        df[variable] = pd.to_numeric(df[variable], errors="raise")
        if df[variable].isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"Valor no finito en {variable}")
    df = df.sort_values(["municipio", "enfermedad", "fecha_semana"]).reset_index(drop=True)
    features = pd.DataFrame(index=df.index, dtype=float)
    continuidad = pd.Series(False, index=df.index, name="historia_4_semanas_completa")
    # Consultas por fecha exacta: incluso con huecos, lag2 significa 14 días.
    for _, grupo in df.groupby(["municipio", "enfermedad"], sort=False):
        fechas = pd.DatetimeIndex(grupo["fecha_semana"])
        anteriores = [fechas - pd.Timedelta(weeks=k) for k in range(1, 5)]
        continuidad.loc[grupo.index] = [
            all(fecha in fechas for fecha in semana) for semana in zip(*anteriores)
        ]
        for variable in variables:
            serie = grupo.set_index("fecha_semana")[variable]
            for k in (2, 3, 4):
                features.loc[grupo.index, f"{variable}_lag{k}"] = serie.reindex(
                    fechas - pd.Timedelta(weeks=k)
                ).to_numpy()
            inicio = 0 if incluir_semana_actual else 1
            for ventana in (2, 3, 4):
                valores = pd.DataFrame({
                    k: serie.reindex(fechas - pd.Timedelta(weeks=k)).to_numpy()
                    for k in range(inicio, inicio + ventana)
                })
                features.loc[grupo.index, f"{variable}_media_movil_{ventana}sem"] = (
                    valores.mean(axis=1).where(valores.notna().all(axis=1)).to_numpy()
                )
            if incluir_semana_actual:
                features.loc[grupo.index, variable] = grupo[variable].to_numpy()
    return ResultadoFeatures(
        claves=df[CLAVES].copy(), features=features,
        objetivos=df[[c for c in OBJETIVOS if c in df]].copy(),
        continuidad=continuidad,
    )


def cargar_features(
    ruta: str | Path = DATASET_DENGUE, *, incluir_semana_actual: bool = False
) -> ResultadoFeatures:
    """Lee un CSV sin modificarlo y genera sus features (TASK-011)."""
    return generar_features(
        pd.read_csv(ruta), incluir_semana_actual=incluir_semana_actual
    )
