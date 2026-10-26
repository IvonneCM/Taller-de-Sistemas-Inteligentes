"""TASK-013: explicaciones locales SHAP de los artefactos de TASK-012.

No entrena, imputa ni escribe archivos. La salida explica el margen binario
en log-odds, no una cantidad de casos ni puntos porcentuales.
"""

from __future__ import annotations

import json
from numbers import Integral
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


def _cargar_artefacto(horizonte: int, directorio: Path | None):
    # Importación diferida: permite validar entradas sin instalar el stack ML.
    from app.ml.entrenamiento import cargar_artefacto

    if directorio is None:
        return cargar_artefacto(horizonte)
    return cargar_artefacto(horizonte, directorio=Path(directorio))


def _validar_datos(datos: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    if not isinstance(datos, pd.DataFrame):
        raise TypeError("Las observaciones deben ser un pandas.DataFrame.")
    if datos.empty:
        raise ValueError("Se requiere al menos una observación.")
    if datos.columns.has_duplicates:
        raise ValueError("Hay columnas duplicadas.")
    faltantes = [c for c in columnas if c not in datos.columns]
    adicionales = [c for c in datos.columns if c not in columnas]
    if faltantes or adicionales:
        raise ValueError(
            f"Columnas faltantes: {faltantes}; adicionales: {adicionales}."
        )
    if list(datos.columns) != columnas:
        raise ValueError("Columnas desordenadas: respete artefacto.features.")
    for columna in columnas:
        dtype = datos[columna].dtype
        if (
            not is_numeric_dtype(dtype)
            or is_bool_dtype(dtype)
            or pd.api.types.is_complex_dtype(dtype)
        ):
            raise TypeError(f"La columna {columna} debe contener números reales.")
    try:
        valores = datos.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Datos incompatibles con XGBoost.") from exc
    if np.isinf(valores).any():
        raise ValueError("Los datos no pueden contener infinitos.")
    # XGBoost representa los predictores mediante float32.
    if (np.abs(valores[~np.isnan(valores)]) > np.finfo(np.float32).max).any():
        raise ValueError("Datos fuera del rango numérico de XGBoost.")
    return pd.DataFrame(valores, columns=columnas, index=datos.index)


def _calcular_shap(artefacto, datos: pd.DataFrame):
    import shap
    import xgboost

    objetivo = json.loads(artefacto.modelo.save_config())["learner"][
        "objective"
    ]["name"]
    if objetivo != "binary:logistic":
        raise ValueError("Solo se admite el objetivo binary:logistic en log_odds.")
    explicador = shap.TreeExplainer(
        artefacto.modelo,
        model_output="raw",
        feature_perturbation="tree_path_dependent",
    )
    pesos = explicador.shap_values(datos, check_additivity=True)
    matriz = xgboost.DMatrix(
        datos, feature_names=artefacto.features, missing=np.nan
    )
    margen = artefacto.modelo.predict(matriz, output_margin=True)
    return pesos, explicador.expected_value, margen


def explicar_observaciones(
    datos: pd.DataFrame,
    horizonte: int,
    *,
    directorio: Path | None = None,
) -> list[dict]:
    """Explica filas en su orden original; exige el esquema exacto del modelo.

    FileNotFoundError indica artefactos ausentes; ImportError indica dependencias
    ausentes. Los errores de carga/SHAP se propagan, sin generar sustitutos.
    RuntimeError indica resultados SHAP incompatibles o no aditivos.
    """
    if (
        isinstance(horizonte, bool)
        or not isinstance(horizonte, Integral)
        or horizonte not in (3, 4)
    ):
        raise ValueError("El horizonte debe ser el entero 3 o 4.")
    if not isinstance(datos, pd.DataFrame):
        raise TypeError("Las observaciones deben ser un pandas.DataFrame.")
    if datos.empty:
        raise ValueError("Se requiere al menos una observación.")
    artefacto = _cargar_artefacto(int(horizonte), directorio)
    X = _validar_datos(datos, artefacto.features)
    pesos, base, margen = _calcular_shap(artefacto, X)
    pesos = np.asarray(pesos, dtype=float)
    base = np.asarray(base, dtype=float)
    margen = np.asarray(margen, dtype=float)
    if pesos.shape != X.shape or base.size != 1 or margen.shape != (len(X),):
        raise RuntimeError("Forma de salida SHAP incompatible con el modelo binario.")
    base = float(base.reshape(-1)[0])
    if not (
        np.isfinite(pesos).all()
        and np.isfinite(base)
        and np.isfinite(margen).all()
    ):
        raise RuntimeError("La explicación contiene resultados no finitos.")
    if not np.allclose(base + pesos.sum(axis=1), margen, rtol=1e-5, atol=1e-5):
        raise RuntimeError("SHAP no cumple la propiedad aditiva en log_odds.")
    respuestas = []
    for fila, salida in zip(pesos, margen):
        ranking = sorted(
            ({"variable": nombre, "peso": float(peso)}
             for nombre, peso in zip(artefacto.features, fila)),
            key=lambda item: abs(item["peso"]), reverse=True,
        )
        respuestas.append({
            "horizonte_semanas": int(horizonte),
            "valor_base": base,
            "salida_modelo": float(salida),
            "escala": "log_odds",
            "explicaciones": ranking,
        })
    return respuestas


def explicar_observacion(
    datos: pd.DataFrame,
    horizonte: int,
    *,
    directorio: Path | None = None,
) -> dict:
    """Explica un DataFrame de exactamente una fila; devuelve un diccionario."""
    if not isinstance(datos, pd.DataFrame):
        raise TypeError("La observación debe ser un pandas.DataFrame de una fila.")
    if len(datos) != 1:
        raise ValueError("Se requiere exactamente una observación.")
    return explicar_observaciones(datos, horizonte, directorio=directorio)[0]
