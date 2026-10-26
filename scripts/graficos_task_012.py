"""TASK-012: gráficos reproducibles del baseline XGBoost de dengue.

Recalcula las predicciones walk-forward (sin tocar la base de datos), las
compara contra la metadata versionada de los artefactos y genera gráficos de
métricas, matrices de confusión, curvas ROC/PR, desempeño por origen,
distribución de probabilidades e importancia de variables.

Entradas:
  dengue-malaria-prediccion/app/ml/artifacts/baseline_dengue_t{3,4}_v1*
  data/processed/panel_semanal_dengue_clima.csv

Salidas (scripts/task_012_output/):
  metricas_comparadas.png
  matrices_confusion.png
  curvas_roc_pr.png
  metricas_por_origen.png
  distribucion_probabilidades.png
  importancia_variables.png
  predicciones_walk_forward_t{3,4}.csv
  metricas_por_origen_t{3,4}.csv
  metricas_agregadas_t{3,4}.csv
  verificacion_metadata.json

Uso, desde la raíz del repositorio:
  python scripts/graficos_task_012.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "dengue-malaria-prediccion"
ARTIFACTS_DIR = BACKEND_DIR / "app" / "ml" / "artifacts"
OUTPUT_DIR = BASE_DIR / "scripts" / "task_012_output"

sys.path.insert(0, str(BACKEND_DIR))

from app.ml import entrenamiento  # noqa: E402
from app.ml.features import cargar_features  # noqa: E402


HORIZONTES = (3, 4)
MODELOS = ("modelo", "clase_mayoritaria", "casos_recientes")
ETIQUETAS = {
    "modelo": "XGBoost baseline",
    "clase_mayoritaria": "Clase mayoritaria",
    "casos_recientes": "Regla casos recientes",
}
COLORES = {
    "modelo": "#1f77b4",
    "clase_mayoritaria": "#7f7f7f",
    "casos_recientes": "#ff7f0e",
}
METRICAS_BARRAS = (
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
)
NOMBRES_METRICAS = {
    "accuracy": "Accuracy",
    "balanced_accuracy": "Balanced acc.",
    "precision": "Precision",
    "recall": "Recall",
    "f1": "F1",
    "roc_auc": "ROC-AUC",
}
CLAVES_VERIFICACION = (
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "pr_auc",
    "brier",
)


def configurar_estilo():
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "legend.frameon": False,
        }
    )


def _ruta_metadata(horizonte):
    return ARTIFACTS_DIR / f"baseline_dengue_t{horizonte}_v1_metadata.json"


def _ruta_modelo(horizonte):
    return ARTIFACTS_DIR / f"baseline_dengue_t{horizonte}_v1.json"


def evaluar_horizonte(resultado, horizonte):
    """Repite el walk-forward y conserva las probabilidades por predicción."""
    etiqueta = entrenamiento.construir_etiqueta(resultado, horizonte)
    particiones = entrenamiento.particiones_walk_forward(
        resultado, horizonte
    )

    predicciones = []
    detalle = []
    y_partes = []
    probabilidades = {nombre: [] for nombre in MODELOS}

    for particion in particiones:
        X_train = resultado.features.loc[particion.train]
        y_train = etiqueta.loc[particion.train]
        X_test = resultado.features.loc[particion.test]
        y_test = etiqueta.loc[particion.test]

        modelo = entrenamiento.construir_modelo()
        modelo.fit(X_train, y_train)
        proba_modelo = modelo.predict_proba(X_test)[:, 1]

        columna = entrenamiento._columna_casos_recientes(X_test)
        proba_recientes = (
            X_test[columna].fillna(0).gt(0).astype(float).to_numpy()
        )
        proba_mayoria = np.full(
            len(y_test), float(y_train.mean()), dtype=float
        )

        metricas = {
            "modelo": entrenamiento.calcular_metricas(
                y_test, proba_modelo
            ),
            "clase_mayoritaria": entrenamiento.calcular_metricas(
                y_test, proba_mayoria
            ),
            "casos_recientes": entrenamiento.calcular_metricas(
                y_test, proba_recientes
            ),
        }
        detalle.append(
            {
                "origen": particion.origen,
                "n_train": int(len(particion.train)),
                "n_test": int(len(particion.test)),
                "metricas": metricas,
            }
        )

        base = resultado.claves.loc[particion.test]
        for indice, y_real, p_modelo, p_mayoria, p_recientes in zip(
            particion.test,
            y_test.to_numpy(dtype=int),
            proba_modelo,
            proba_mayoria,
            proba_recientes,
        ):
            predicciones.append(
                {
                    "origen": particion.origen.date().isoformat(),
                    "municipio": base.loc[indice, "municipio"],
                    "fecha_semana": base.loc[
                        indice, "fecha_semana"
                    ].date().isoformat(),
                    "y_real": int(y_real),
                    "p_modelo": float(p_modelo),
                    "p_mayoria": float(p_mayoria),
                    "p_recientes": float(p_recientes),
                }
            )

        y_partes.append(y_test.to_numpy(dtype=int))
        probabilidades["modelo"].append(proba_modelo)
        probabilidades["clase_mayoritaria"].append(proba_mayoria)
        probabilidades["casos_recientes"].append(proba_recientes)

    y_all = np.concatenate(y_partes)
    p_all = {
        nombre: np.concatenate(valores)
        for nombre, valores in probabilidades.items()
    }
    macro = {
        nombre: entrenamiento._promediar_metricas(
            [fila["metricas"][nombre] for fila in detalle]
        )
        for nombre in MODELOS
    }
    pooled = {
        nombre: entrenamiento.calcular_metricas(y_all, p_all[nombre])
        for nombre in MODELOS
    }

    return {
        "predicciones": pd.DataFrame(predicciones),
        "detalle": detalle,
        "macro": macro,
        "pooled": pooled,
        "y": y_all,
        "p": p_all,
    }


def verificar_metadata(resumenes):
    """Comprueba que el recálculo coincide con los artefactos versionados."""
    verificacion = {}
    for horizonte in HORIZONTES:
        metadata = json.loads(
            _ruta_metadata(horizonte).read_text(encoding="utf-8")
        )
        esperado = metadata["validacion"]["agregado"]
        resumen = resumenes[horizonte]
        diferencias = {}
        for nombre in MODELOS:
            for tipo in ("macro", "pooled"):
                for clave in CLAVES_VERIFICACION:
                    valor_esperado = esperado[nombre][tipo][clave]
                    valor_obtenido = resumen[tipo][nombre][clave]
                    if valor_esperado is None or valor_obtenido is None:
                        if valor_esperado != valor_obtenido:
                            diferencias[f"{nombre}.{tipo}.{clave}"] = {
                                "esperado": valor_esperado,
                                "obtenido": valor_obtenido,
                            }
                        continue
                    diferencia = abs(
                        float(valor_esperado) - float(valor_obtenido)
                    )
                    if diferencia > 1e-4:
                        diferencias[f"{nombre}.{tipo}.{clave}"] = {
                            "esperado": valor_esperado,
                            "obtenido": valor_obtenido,
                        }
        verificacion[f"t+{horizonte}"] = {
            "coincide_con_metadata": not diferencias,
            "diferencias": diferencias,
        }
        if diferencias:
            raise RuntimeError(
                f"El recálculo de t+{horizonte} no coincide con la metadata: "
                f"{diferencias}"
            )
    return verificacion


def _guardar(figura, nombre):
    ruta = OUTPUT_DIR / nombre
    figura.savefig(ruta, bbox_inches="tight", dpi=150)
    plt.close(figura)
    print(f"  {ruta.name}")


def grafico_metricas(resumenes):
    fig, ejes = plt.subplots(1, 2, figsize=(14, 5.2), sharey=True)
    ancho = 0.26
    posiciones = np.arange(len(METRICAS_BARRAS))

    for eje, horizonte in zip(ejes, HORIZONTES):
        macro = resumenes[horizonte]["macro"]
        for desplazamiento, nombre in zip((-1, 0, 1), MODELOS):
            valores = [
                macro[nombre][metrica] or 0.0
                for metrica in METRICAS_BARRAS
            ]
            barras = eje.bar(
                posiciones + desplazamiento * ancho,
                valores,
                ancho,
                label=ETIQUETAS[nombre],
                color=COLORES[nombre],
                edgecolor="white",
                linewidth=0.5,
            )
            for barra, valor in zip(barras, valores):
                eje.text(
                    barra.get_x() + barra.get_width() / 2,
                    valor + 0.015,
                    f"{valor:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                )
        eje.set_xticks(posiciones)
        eje.set_xticklabels(
            [NOMBRES_METRICAS[m] for m in METRICAS_BARRAS],
            rotation=20,
            ha="right",
        )
        eje.set_ylim(0, 1.12)
        eje.set_title(f"t+{horizonte}: promedio macro por origen")
        eje.legend(loc="upper right", fontsize=8)

    ejes[0].set_ylabel("Valor (0 a 1)")
    fig.suptitle(
        "Modelo vs baselines: métricas de validación walk-forward",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    _guardar(fig, "metricas_comparadas.png")


def grafico_matrices_confusion(resumenes):
    fig, ejes = plt.subplots(2, 3, figsize=(12, 8))
    for fila, horizonte in enumerate(HORIZONTES):
        for columna, nombre in enumerate(MODELOS):
            eje = ejes[fila, columna]
            metrica = resumenes[horizonte]["macro"][nombre]
            matriz = metrica["matriz_confusion"]
            cm = np.array(
                [
                    [matriz["tn"], matriz["fp"]],
                    [matriz["fn"], matriz["tp"]],
                ]
            )
            maximo = cm.max() if cm.max() else 1
            eje.imshow(cm, cmap="Blues", vmin=0, vmax=maximo)
            for (y, x), valor in np.ndenumerate(cm):
                eje.text(
                    x,
                    y,
                    str(int(valor)),
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    color="white" if valor > maximo / 2 else "black",
                )
            eje.set_xticks([0, 1])
            eje.set_yticks([0, 1])
            eje.set_xticklabels(["Pred. negativo", "Pred. positivo"])
            eje.set_yticklabels(["Real negativo", "Real positivo"])
            eje.set_xlabel("Predicción")
            eje.set_ylabel("Resultado real")
            eje.set_title(
                f"t+{horizonte} · {ETIQUETAS[nombre]}\n"
                f"F1={metrica['f1']:.3f} · Accuracy={metrica['accuracy']:.3f}"
            )
            eje.grid(False)

    fig.suptitle(
        "Matrices de confusión agregadas del walk-forward",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _guardar(fig, "matrices_confusion.png")


def grafico_curvas_roc_pr(resumenes):
    fig, ejes = plt.subplots(2, 2, figsize=(11, 9))

    for columna, horizonte in enumerate(HORIZONTES):
        y = resumenes[horizonte]["y"]
        p = resumenes[horizonte]["p"]

        eje = ejes[0, columna]
        for nombre in MODELOS:
            fpr, tpr, _ = roc_curve(y, p[nombre])
            auc = roc_auc_score(y, p[nombre])
            eje.plot(
                fpr,
                tpr,
                label=f"{ETIQUETAS[nombre]} (AUC={auc:.3f})",
                color=COLORES[nombre],
                linewidth=2.2 if nombre == "modelo" else 1.4,
            )
        eje.plot([0, 1], [0, 1], "--", color="black", linewidth=0.8)
        eje.set_xlim(0, 1)
        eje.set_ylim(0, 1.02)
        eje.set_xlabel("Tasa de falsos positivos")
        eje.set_ylabel("Tasa de verdaderos positivos")
        eje.set_title(f"Curva ROC · t+{horizonte}")
        eje.legend(loc="lower right", fontsize=8)

        eje = ejes[1, columna]
        for nombre in MODELOS:
            precision, recall, _ = precision_recall_curve(y, p[nombre])
            ap = average_precision_score(y, p[nombre])
            eje.plot(
                recall,
                precision,
                label=f"{ETIQUETAS[nombre]} (AP={ap:.3f})",
                color=COLORES[nombre],
                linewidth=2.2 if nombre == "modelo" else 1.4,
            )
        eje.axhline(
            y.mean(),
            linestyle=":",
            color="black",
            linewidth=0.9,
            label=f"Prevalencia ({y.mean():.3f})",
        )
        eje.set_xlim(0, 1)
        eje.set_ylim(0, 1.02)
        eje.set_xlabel("Recall")
        eje.set_ylabel("Precision")
        eje.set_title(f"Curva precision-recall · t+{horizonte}")
        eje.legend(loc="lower left", fontsize=8)

    fig.suptitle(
        "Capacidad de discriminación sobre predicciones agrupadas",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _guardar(fig, "curvas_roc_pr.png")


def grafico_por_origen(resumenes):
    fig, ejes = plt.subplots(2, 2, figsize=(12, 8), sharey="row")
    ancho = 0.26

    for columna, horizonte in enumerate(HORIZONTES):
        detalle = resumenes[horizonte]["detalle"]
        posiciones = np.arange(len(detalle))
        etiquetas_origen = [
            fila["origen"].strftime("%d-%m") for fila in detalle
        ]
        for fila, metrica in enumerate(("f1", "roc_auc")):
            eje = ejes[fila, columna]
            for desplazamiento, nombre in zip((-1, 0, 1), MODELOS):
                valores = [
                    dato["metricas"][nombre][metrica] or 0.0
                    for dato in detalle
                ]
                eje.bar(
                    posiciones + desplazamiento * ancho,
                    valores,
                    ancho,
                    label=ETIQUETAS[nombre],
                    color=COLORES[nombre],
                    edgecolor="white",
                    linewidth=0.5,
                )
            if metrica == "roc_auc":
                eje.axhline(
                    0.5,
                    color="black",
                    linestyle="--",
                    linewidth=0.8,
                    alpha=0.7,
                )
            eje.set_xticks(posiciones)
            eje.set_xticklabels(etiquetas_origen)
            eje.set_ylim(0, 1.05)
            eje.set_xlabel("Origen de predicción (día-mes de 2026)")
            eje.set_ylabel(metrica.upper())
            eje.set_title(f"{metrica.upper()} por origen · t+{horizonte}")
            if fila == 0 and columna == 0:
                eje.legend(loc="upper right", fontsize=8)

    fig.suptitle(
        "Variabilidad del desempeño entre orígenes walk-forward",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _guardar(fig, "metricas_por_origen.png")


def grafico_distribuciones(resumenes):
    fig, ejes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    bins = np.linspace(0, 1, 11)

    for eje, horizonte in zip(ejes, HORIZONTES):
        predicciones = resumenes[horizonte]["predicciones"]
        negativos = predicciones.loc[
            predicciones["y_real"] == 0, "p_modelo"
        ]
        positivos = predicciones.loc[
            predicciones["y_real"] == 1, "p_modelo"
        ]
        eje.hist(
            negativos,
            bins=bins,
            alpha=0.65,
            color="#4c78a8",
            edgecolor="white",
            label=f"Real negativo (n={len(negativos)})",
        )
        eje.hist(
            positivos,
            bins=bins,
            alpha=0.65,
            color="#e45756",
            edgecolor="white",
            label=f"Real positivo (n={len(positivos)})",
        )
        eje.axvline(
            0.5,
            color="black",
            linestyle="--",
            linewidth=1,
            label="Umbral 0.5",
        )
        eje.set_xlim(0, 1)
        eje.set_xlabel("Probabilidad predicha: P(≥1 caso)")
        eje.set_ylabel("Municipio-semanas")
        eje.set_title(f"Distribución de probabilidades · t+{horizonte}")
        eje.legend(loc="upper center", fontsize=8)

    fig.suptitle(
        "Separación de clases: probabilidad del modelo según el resultado real",
        fontsize=13,
        y=1.03,
    )
    fig.tight_layout()
    _guardar(fig, "distribucion_probabilidades.png")


def grafico_importancia():
    fig, ejes = plt.subplots(1, 2, figsize=(14, 6.5))

    for eje, horizonte in zip(ejes, HORIZONTES):
        booster = xgboost.Booster()
        booster.load_model(_ruta_modelo(horizonte))
        ganancias = booster.get_score(importance_type="gain")
        total = sum(ganancias.values()) or 1.0
        principales = sorted(
            ganancias.items(), key=lambda item: item[1]
        )[-15:]
        nombres = [nombre for nombre, _ in principales]
        valores = [valor / total for _, valor in principales]
        eje.barh(
            nombres,
            valores,
            color="#4c78a8",
            edgecolor="white",
            linewidth=0.5,
        )
        eje.set_xlabel("Ganancia relativa sobre el total")
        eje.set_title(
            f"Importancia de variables · t+{horizonte} (top 15)"
        )
        eje.grid(axis="y", visible=False)
        for posicion, valor in enumerate(valores):
            eje.text(
                valor + 0.002,
                posicion,
                f"{valor:.1%}",
                va="center",
                fontsize=7,
            )

    fig.suptitle(
        "Qué variables usó el modelo final (ganancia de XGBoost, no SHAP)",
        fontsize=13,
        y=1.01,
    )
    fig.tight_layout()
    _guardar(fig, "importancia_variables.png")


def guardar_tablas(resumenes):
    for horizonte in HORIZONTES:
        resumen = resumenes[horizonte]
        resumen["predicciones"].to_csv(
            OUTPUT_DIR / f"predicciones_walk_forward_t{horizonte}.csv",
            index=False,
        )

        filas = []
        for dato in resumen["detalle"]:
            for nombre in MODELOS:
                fila = {
                    "origen": dato["origen"].date().isoformat(),
                    "n_train": dato["n_train"],
                    "n_test": dato["n_test"],
                    "modelo": nombre,
                }
                fila.update(dato["metricas"][nombre])
                filas.append(fila)
        pd.DataFrame(filas).to_csv(
            OUTPUT_DIR / f"metricas_por_origen_t{horizonte}.csv",
            index=False,
        )

        filas = []
        for nombre in MODELOS:
            fila = {"modelo": nombre}
            fila.update(resumen["macro"][nombre])
            filas.append(fila)
        pd.DataFrame(filas).to_csv(
            OUTPUT_DIR / f"metricas_agregadas_t{horizonte}.csv",
            index=False,
        )


def main():
    configurar_estilo()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Cargando features...")
    resultado = cargar_features()

    print("Recalculando walk-forward...")
    resumenes = {
        horizonte: evaluar_horizonte(resultado, horizonte)
        for horizonte in HORIZONTES
    }

    print("Verificando contra metadata versionada...")
    verificacion = verificar_metadata(resumenes)
    (OUTPUT_DIR / "verificacion_metadata.json").write_text(
        json.dumps(verificacion, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Generando tablas...")
    guardar_tablas(resumenes)

    print("Generando gráficos...")
    grafico_metricas(resumenes)
    grafico_matrices_confusion(resumenes)
    grafico_curvas_roc_pr(resumenes)
    grafico_por_origen(resumenes)
    grafico_distribuciones(resumenes)
    grafico_importancia()

    print(f"\nListo. Salidas en {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
