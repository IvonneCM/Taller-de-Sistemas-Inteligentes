"""TASK-012 / NFR-001, NFR-002: baseline XGBoost de dengue, offline.

Entrena dos clasificadores binarios, uno por horizonte (t+3 y t+4), usando
exclusivamente las features de `app.ml.features` (TASK-011). La etiqueta es
`casos_dengue_t_mas_{h} > 0`; es una marca de "hubo al menos un caso", NO una
definicion epidemiologica de brote.

La validacion es walk-forward por fecha: para cada origen de prediccion se
entrena solo con filas cuyo objetivo ya estaria disponible segun la hipotesis
`fecha_semana + horizonte + 1 <= origen`. Nunca se mezcla futuro en train ni
se usa una division aleatoria. Los faltantes no se imputan: XGBoost los
maneja de forma nativa.

Este modulo no accede a la base de datos durante el entrenamiento. El
registro opcional en `modelos.metricas_entrenamiento` (TASK-012) se hace con
`--registrar-bd` y requiere `DATABASE_URL`.

Uso:
    python -m app.ml.entrenamiento --todos --guardar
    python -m app.ml.entrenamiento --horizonte 3 --guardar --registrar-bd
"""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from app.ml.features import (
    DATASET_DENGUE,
    ResultadoFeatures,
    cargar_features,
)


ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_VERSION = "v1"
ENFERMEDAD = "dengue"
HORIZONTES = (3, 4)
RETRASO_SEMANAS = 0
UMBRAL_PROBABILIDAD = 0.5

HIPERPARAMETROS = {
    "n_estimators": 200,
    "max_depth": 2,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "min_child_weight": 1,
    "reg_lambda": 1.0,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "tree_method": "hist",
    "random_state": 42,
    "n_jobs": 1,
}

ADVERTENCIAS = (
    "La etiqueta 'hay_casos_t_mas_N' indica al menos un caso; no es una "
    "definicion de brote epidemiologico.",
    "El panel cubre solo SE1-SE13 de 2026; no hay ciclo anual ni validacion "
    "entre anios.",
    "Los casos historicos pueden haber sido corregidos retrospectivamente y "
    "no representan los datos disponibles en tiempo real.",
    "El clima de NASA POWER es modelado, no observado.",
    "Las metricas son exploratorias y no validan NFR-001 ni NFR-002.",
    "El protocolo de disponibilidad (semana + horizonte + 1) es una "
    "hipotesis de evaluacion, no una fecha de publicacion confirmada.",
    "No se imputan valores faltantes; XGBoost los maneja de forma nativa.",
)


@dataclass
class Particion:
    """Indices de entrenamiento y prueba para un origen de prediccion."""

    origen: pd.Timestamp
    train: pd.Index
    test: pd.Index


@dataclass
class ArtefactoBaseline:
    """Booster XGBoost y su metadata, listos para TASK-014/SHAP."""

    horizonte: int
    modelo: xgboost.Booster
    features: list[str]
    metadata: dict
    ruta_modelo: Path


def construir_etiqueta(
    resultado: ResultadoFeatures, horizonte: int
) -> pd.Series:
    """Devuelve 1.0/0.0/NaN para el objetivo del horizonte indicado."""
    if horizonte not in HORIZONTES:
        raise ValueError("El horizonte debe ser 3 o 4.")
    columna = f"casos_dengue_t_mas_{horizonte}"
    if columna not in resultado.objetivos:
        raise ValueError(f"El panel no contiene el objetivo {columna}.")
    casos = resultado.objetivos[columna]
    etiqueta = pd.Series(np.nan, index=casos.index, dtype=float, name=columna)
    conocidos = casos.notna()
    etiqueta.loc[conocidos] = (casos.loc[conocidos] > 0).astype(float)
    return etiqueta


def particiones_walk_forward(
    resultado: ResultadoFeatures,
    horizonte: int,
    *,
    retraso_semanas: int = RETRASO_SEMANAS,
    exigir_historia_completa: bool = False,
) -> list[Particion]:
    """Construye origenes donde train y test no comparten futuro.

    Una fila de la semana t es elegible para test en el origen O solo si
    t == O y su objetivo existe. Para train, ademas, su objetivo debe estar
    disponible en O: t + horizonte + 1 + retraso <= O.
    """
    if horizonte not in HORIZONTES:
        raise ValueError("El horizonte debe ser 3 o 4.")
    if not isinstance(retraso_semanas, int) or retraso_semanas < 0:
        raise ValueError("retraso_semanas debe ser un entero no negativo.")

    fechas = resultado.claves["fecha_semana"]
    etiqueta = construir_etiqueta(resultado, horizonte)
    conocidas = resultado.features.notna()
    historia = (
        conocidas.all(axis=1)
        if exigir_historia_completa
        else conocidas.any(axis=1)
    )
    elegibles = historia & etiqueta.notna()
    disponible = fechas + pd.Timedelta(
        weeks=horizonte + 1 + retraso_semanas
    )

    particiones: list[Particion] = []
    for origen in sorted(fechas.unique()):
        train = elegibles & disponible.le(origen)
        test = elegibles & fechas.eq(origen)
        if train.any() and test.any():
            particiones.append(
                Particion(
                    origen=pd.Timestamp(origen),
                    train=resultado.features.index[train],
                    test=resultado.features.index[test],
                )
            )
    if not particiones:
        raise ValueError(
            "No hay origenes con train y test no vacios para este horizonte."
        )
    return particiones


def construir_modelo() -> XGBClassifier:
    """Crea el clasificador con parametros fijos y reproducibles."""
    return XGBClassifier(**HIPERPARAMETROS)


def calcular_metricas(
    y_true: pd.Series | np.ndarray,
    probabilidad: np.ndarray,
    *,
    umbral: float = UMBRAL_PROBABILIDAD,
) -> dict:
    """Metricas de clasificacion binaria con umbral explicito."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probabilidad, dtype=float)
    if len(y) != len(proba):
        raise ValueError("y_true y probabilidad deben tener el mismo largo.")
    if len(y) == 0:
        raise ValueError("No hay filas para evaluar.")

    pred = (proba >= umbral).astype(int)
    positivos = int(y.sum())
    negativos = int(len(y) - positivos)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()

    dos_clases = positivos > 0 and negativos > 0
    return {
        "n": int(len(y)),
        "positivos": positivos,
        "negativos": negativos,
        "prevalencia": round(float(y.mean()), 4),
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(y, pred)) if dos_clases else 0.0, 4
        ),
        "precision": round(
            float(precision_score(y, pred, zero_division=0)), 4
        ),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "roc_auc": (
            round(float(roc_auc_score(y, proba)), 4) if dos_clases else None
        ),
        "pr_auc": (
            round(float(average_precision_score(y, proba)), 4)
            if dos_clases
            else None
        ),
        "brier": round(float(brier_score_loss(y, proba)), 4),
        "matriz_confusion": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
        },
    }


def _columna_casos_recientes(X: pd.DataFrame) -> str | None:
    for columna in (
        "casos_dengue_media_movil_2sem",
        "casos_dengue_lag2",
    ):
        if columna in X.columns:
            return columna
    return None


def calcular_baselines(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, dict]:
    """Baselines comparables: clase mayoritaria y regla de casos recientes."""
    salida: dict[str, dict] = {}

    prevalencia_train = float(y_train.mean())
    proba_mayoria = np.full(len(y_test), prevalencia_train, dtype=float)
    salida["clase_mayoritaria"] = calcular_metricas(y_test, proba_mayoria)

    columna = _columna_casos_recientes(X_test)
    if columna is not None:
        proba_regla = (
            X_test[columna].fillna(0).gt(0).astype(float).to_numpy()
        )
        salida["casos_recientes"] = calcular_metricas(y_test, proba_regla)

    return salida


def _acumular(
    y_true: list[np.ndarray], probabilidad: list[np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    return np.concatenate(y_true), np.concatenate(probabilidad)


def _promediar_metricas(metricas: list[dict]) -> dict:
    """Macro-promedio de metricas por origen (evita mezclar prevalencias)."""
    if not metricas:
        raise ValueError("No hay metricas para promediar.")
    salida: dict = {
        "n_origenes": len(metricas),
        "n": int(sum(m["n"] for m in metricas)),
        "positivos": int(sum(m["positivos"] for m in metricas)),
        "negativos": int(sum(m["negativos"] for m in metricas)),
    }
    salida["prevalencia"] = round(
        salida["positivos"] / salida["n"] if salida["n"] else 0.0, 4
    )
    for clave in (
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
        "brier",
    ):
        valores = [m[clave] for m in metricas if m.get(clave) is not None]
        salida[clave] = (
            round(float(np.mean(valores)), 4) if valores else None
        )
    salida["matriz_confusion"] = {
        clave: int(sum(m["matriz_confusion"][clave] for m in metricas))
        for clave in ("tn", "fp", "fn", "tp")
    }
    return salida


def _entrenar_y_evaluar(
    resultado: ResultadoFeatures,
    horizonte: int,
    *,
    retraso_semanas: int = RETRASO_SEMANAS,
    exigir_historia_completa: bool = False,
) -> tuple[list[dict], dict]:
    """Ejecuta walk-forward y devuelve detalle por origen y agregado."""
    etiqueta = construir_etiqueta(resultado, horizonte)
    particiones = particiones_walk_forward(
        resultado,
        horizonte,
        retraso_semanas=retraso_semanas,
        exigir_historia_completa=exigir_historia_completa,
    )

    detalle: list[dict] = []
    y_eval: list[np.ndarray] = []
    p_modelo: list[np.ndarray] = []
    p_base: dict[str, list[np.ndarray]] = {}

    for particion in particiones:
        X_train = resultado.features.loc[particion.train]
        y_train = etiqueta.loc[particion.train]
        X_test = resultado.features.loc[particion.test]
        y_test = etiqueta.loc[particion.test]

        modelo = construir_modelo()
        modelo.fit(X_train, y_train)
        proba = modelo.predict_proba(X_test)[:, 1]

        metricas_modelo = calcular_metricas(y_test, proba)
        baselines = calcular_baselines(X_train, y_train, X_test, y_test)

        detalle.append(
            {
                "origen": particion.origen.date().isoformat(),
                "n_train": int(len(particion.train)),
                "n_test": int(len(particion.test)),
                "positivos_train": int(y_train.sum()),
                "positivos_test": int(y_test.sum()),
                "modelo": metricas_modelo,
                "baselines": baselines,
            }
        )

        y_eval.append(y_test.to_numpy(dtype=int))
        p_modelo.append(proba)
        for nombre in baselines:
            if nombre not in p_base:
                p_base[nombre] = []
            if nombre == "clase_mayoritaria":
                p_base[nombre].append(
                    np.full(len(y_test), float(y_train.mean()))
                )
            else:
                columna = _columna_casos_recientes(X_test)
                p_base[nombre].append(
                    X_test[columna].fillna(0).gt(0).astype(float).to_numpy()
                )

    y_all, p_all = _acumular(y_eval, p_modelo)
    y_base_all = np.concatenate(y_eval)
    agregado: dict[str, dict] = {
        "modelo": {
            "pooled": calcular_metricas(y_all, p_all),
            "macro": _promediar_metricas(
                [fila["modelo"] for fila in detalle]
            ),
        }
    }
    for nombre, lista in p_base.items():
        agregado[nombre] = {
            "pooled": calcular_metricas(
                y_base_all, np.concatenate(lista)
            ),
            "macro": _promediar_metricas(
                [
                    fila["baselines"][nombre]
                    for fila in detalle
                    if nombre in fila["baselines"]
                ]
            ),
        }
    return detalle, agregado


def _entrenar_final(
    resultado: ResultadoFeatures, horizonte: int
) -> tuple[XGBClassifier, pd.Index]:
    """Entrena el artefacto final con todas las filas con objetivo conocido."""
    etiqueta = construir_etiqueta(resultado, horizonte)
    elegibles = resultado.features.notna().any(axis=1) & etiqueta.notna()
    if not elegibles.any():
        raise ValueError("No hay filas elegibles para el modelo final.")
    modelo = construir_modelo()
    modelo.fit(
        resultado.features.loc[elegibles], etiqueta.loc[elegibles]
    )
    return modelo, resultado.features.index[elegibles]


def _metadata(
    resultado: ResultadoFeatures,
    horizonte: int,
    detalle: list[dict],
    agregado: dict,
    filas_final: pd.Index,
    *,
    retraso_semanas: int,
    exigir_historia_completa: bool,
) -> dict:
    features = list(resultado.features.columns)
    fechas = resultado.claves["fecha_semana"]
    return {
        "tarea": "TASK-012",
        "nombre": f"xgboost_baseline_dengue_t{horizonte}",
        "version": MODEL_VERSION,
        "enfermedad": ENFERMEDAD,
        "horizonte_semanas": horizonte,
        "etiqueta": f"casos_dengue_t_mas_{horizonte} > 0",
        "es_definicion_de_brote": False,
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        "features": features,
        "n_features": len(features),
        "retraso_semanas": retraso_semanas,
        "exigir_historia_completa": exigir_historia_completa,
        "umbral_probabilidad": UMBRAL_PROBABILIDAD,
        "hiperparametros": dict(HIPERPARAMETROS),
        "datos": {
            "archivo": DATASET_DENGUE.name,
            "filas_panel": int(len(resultado.features)),
            "filas_entrenamiento_final": int(len(filas_final)),
            "municipios": int(resultado.claves["municipio"].nunique()),
            "primera_semana": fechas.min().date().isoformat(),
            "ultima_semana": fechas.max().date().isoformat(),
        },
        "validacion": {
            "protocolo": (
                "walk-forward por fecha; train solo con objetivos "
                "disponibles en el origen"
            ),
            "origenes": [fila["origen"] for fila in detalle],
            "por_origen": detalle,
            "agregado": agregado,
        },
        "advertencias": list(ADVERTENCIAS),
        "entorno": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "xgboost": xgboost.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def guardar_artefacto(
    modelo: XGBClassifier,
    metadata: dict,
    *,
    directorio: Path = ARTIFACTS_DIR,
) -> tuple[Path, Path]:
    """Guarda el modelo en JSON nativo de XGBoost y su metadata."""
    directorio.mkdir(parents=True, exist_ok=True)
    horizonte = metadata["horizonte_semanas"]
    version = metadata["version"]
    base = f"baseline_dengue_t{horizonte}_{version}"
    ruta_modelo = directorio / f"{base}.json"
    ruta_metadata = directorio / f"{base}_metadata.json"
    modelo.get_booster().save_model(ruta_modelo)
    with ruta_metadata.open("w", encoding="utf-8") as archivo:
        json.dump(metadata, archivo, ensure_ascii=False, indent=2)
    return ruta_modelo, ruta_metadata


def cargar_artefacto(
    horizonte: int,
    *,
    version: str = MODEL_VERSION,
    directorio: Path = ARTIFACTS_DIR,
) -> ArtefactoBaseline:
    """Carga el modelo y valida que conserve el orden de features."""
    if horizonte not in HORIZONTES:
        raise ValueError("El horizonte debe ser 3 o 4.")
    base = f"baseline_dengue_t{horizonte}_{version}"
    ruta_modelo = directorio / f"{base}.json"
    ruta_metadata = directorio / f"{base}_metadata.json"
    if not ruta_modelo.exists() or not ruta_metadata.exists():
        raise FileNotFoundError(
            f"No existe el artefacto {base} en {directorio}."
        )
    with ruta_metadata.open(encoding="utf-8") as archivo:
        metadata = json.load(archivo)
    modelo = xgboost.Booster()
    modelo.load_model(ruta_modelo)
    features = list(metadata["features"])
    if list(modelo.feature_names or []) != features:
        raise ValueError("El orden de features del artefacto no coincide.")
    return ArtefactoBaseline(
        horizonte=horizonte,
        modelo=modelo,
        features=features,
        metadata=metadata,
        ruta_modelo=ruta_modelo,
    )


def predecir_probabilidad(
    artefacto: ArtefactoBaseline, features: pd.DataFrame
) -> np.ndarray:
    """Devuelve P(>=1 caso en t+h) respetando el orden de features."""
    faltantes = [c for c in artefacto.features if c not in features.columns]
    if faltantes:
        raise ValueError(f"Faltan features: {faltantes}")
    matriz = xgboost.DMatrix(
        features[artefacto.features],
        feature_names=artefacto.features,
        missing=np.nan,
    )
    return artefacto.modelo.predict(matriz)


def registrar_metricas_bd(metadata: dict, *, session=None) -> int:
    """Inserta una fila en `modelos` con las metricas del entrenamiento."""
    from app.core.database import SessionLocal
    from app.models import Enfermedad, Modelo

    propia = session is None
    if propia:
        session = SessionLocal()
    try:
        enfermedad = (
            session.query(Enfermedad)
            .filter_by(nombre=metadata["enfermedad"])
            .one_or_none()
        )
        if enfermedad is None:
            raise ValueError(
                "La enfermedad no existe en el catalogo; ejecutar el seed."
            )
        fila = Modelo(
            nombre=metadata["nombre"],
            version=metadata["version"],
            enfermedad_id=enfermedad.id,
            fecha_entrenamiento=datetime.fromisoformat(
                metadata["fecha_entrenamiento"]
            ),
            metricas_entrenamiento=metadata,
        )
        session.add(fila)
        session.flush()
        if propia:
            session.commit()
        return int(fila.id)
    finally:
        if propia:
            session.close()


def ejecutar_horizonte(
    resultado: ResultadoFeatures,
    horizonte: int,
    *,
    retraso_semanas: int = RETRASO_SEMANAS,
    exigir_historia_completa: bool = False,
    guardar: bool = False,
    registrar_bd: bool = False,
    directorio: Path = ARTIFACTS_DIR,
) -> dict:
    """Entrena, evalua y opcionalmente guarda/registra un horizonte."""
    detalle, agregado = _entrenar_y_evaluar(
        resultado,
        horizonte,
        retraso_semanas=retraso_semanas,
        exigir_historia_completa=exigir_historia_completa,
    )
    modelo, filas_final = _entrenar_final(resultado, horizonte)
    metadata = _metadata(
        resultado,
        horizonte,
        detalle,
        agregado,
        filas_final,
        retraso_semanas=retraso_semanas,
        exigir_historia_completa=exigir_historia_completa,
    )
    if guardar or registrar_bd:
        guardar_artefacto(modelo, metadata, directorio=directorio)
    if registrar_bd:
        metadata["modelo_id_bd"] = registrar_metricas_bd(metadata)
    return metadata


def _imprimir_resumen(metadata: dict) -> None:
    horizonte = metadata["horizonte_semanas"]
    agregado = metadata["validacion"]["agregado"]
    modelo = agregado["modelo"]
    print(f"\nHorizonte t+{horizonte} | {metadata['etiqueta']}")
    print(
        f"  Walk-forward: {len(metadata['validacion']['origenes'])} origenes, "
        f"n={modelo['pooled']['n']} predicciones, "
        f"prevalencia={modelo['pooled']['prevalencia']}"
    )
    for nombre, valores in agregado.items():
        pooled = valores["pooled"]
        macro = valores["macro"]
        etiqueta = "Modelo" if nombre == "modelo" else f"Baseline {nombre}"
        print(
            f"  {etiqueta}: pooled F1={pooled['f1']} recall={pooled['recall']} "
            f"precision={pooled['precision']} ROC-AUC={pooled['roc_auc']} "
            f"Brier={pooled['brier']} | macro F1={macro['f1']} "
            f"ROC-AUC={macro['roc_auc']} Brier={macro['brier']}"
        )
    print(
        f"  Filas del modelo final: {metadata['datos']['filas_entrenamiento_final']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Entrena el baseline XGBoost de dengue (TASK-012)."
    )
    parser.add_argument(
        "--horizonte", type=int, choices=list(HORIZONTES), default=None
    )
    parser.add_argument(
        "--todos", action="store_true", help="Entrena t+3 y t+4."
    )
    parser.add_argument(
        "--guardar", action="store_true", help="Guarda modelo y metadata."
    )
    parser.add_argument(
        "--registrar-bd",
        action="store_true",
        help="Inserta las metricas en la tabla modelos (requiere DATABASE_URL).",
    )
    parser.add_argument(
        "--historia-completa",
        action="store_true",
        help="Exige las 24 features no nulas en entrenamiento.",
    )
    parser.add_argument(
        "--retraso-semanas",
        type=int,
        default=RETRASO_SEMANAS,
        help="Semanas adicionales de retraso de reporte (hipotesis).",
    )
    args = parser.parse_args(argv)

    if args.todos and args.horizonte is not None:
        parser.error("Usar --todos o --horizonte, no ambos.")
    if not args.todos and args.horizonte is None:
        parser.error("Indicar --todos o --horizonte 3|4.")
    if args.retraso_semanas < 0:
        parser.error("--retraso-semanas debe ser >= 0.")

    resultado = cargar_features()
    horizontes = HORIZONTES if args.todos else (args.horizonte,)
    salidas = []
    for horizonte in horizontes:
        metadata = ejecutar_horizonte(
            resultado,
            horizonte,
            retraso_semanas=args.retraso_semanas,
            exigir_historia_completa=args.historia_completa,
            guardar=args.guardar,
            registrar_bd=args.registrar_bd,
        )
        _imprimir_resumen(metadata)
        salidas.append(metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
