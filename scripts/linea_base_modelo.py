"""
Linea Base - Paso 3: referencia inicial y registro de experimentos.

Sistema de Prediccion Temprana de Brotes de Dengue y Malaria
Responsable: Ivonne Colque 

Este script NO entrena el modelo del producto. Construye la referencia
verificable inicial (baseline) con los datos reales disponibles y documenta,
con numeros reproducibles, por que todavia no es posible entrenar el modelo
municipio-semana.

Experimentos:
  A. Persistencia (naive) sobre la serie nacional semanal de dengue.
  B. Comparacion walk-forward: media expansiva, tendencia lineal y AR(1).
  C. Regresion cross-sectional (clima -> casos acumulados) y su fallo por
     muestra insuficiente (n=4 dengue, n=3 malaria), con LOOCV.
  D. Protocolo de linea base para cuando exista la serie municipio-semana.

Entradas:
  data/processed/dengue_semanal_validado.csv
  data/processed/dataset_integrado_municipal.csv

Salidas (scripts/linea_base_output/):
  expA_persistencia_nacional.csv
  expA_persistencia_nacional.png        grafico real vs persistencia
  expB_modelos_nacional.csv
  expB_resumen_modelos.csv
  expB_comparacion_modelos.png          barras MAE/RMSE/MAPE por modelo
  expC_cross_sectional.csv
  expC_inviabilidad_municipal.png       R2 / grados de libertad / LOOCV por modelo
  protocolo_baseline.json
  resumen_baseline.json
  linea_base_nacional.png               serie nacional con predicciones

Transparencia de IA: borrador generado con asistencia de IA (opencode/Claude)
y revisado por Ivonne Colque  antes de su publicacion.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "linea_base_output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

DENGUE_SEMANAL = os.path.join(PROCESSED_DIR, "dengue_semanal_validado.csv")
DATASET_INTEGRADO = os.path.join(PROCESSED_DIR, "dataset_integrado_municipal.csv")

VENTANA_INICIAL = 5


# ============================================================
# METRICAS
# ============================================================

def mae(real, pred):
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    return float(np.mean(np.abs(real - pred)))


def rmse(real, pred):
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    return float(np.sqrt(np.mean((real - pred) ** 2)))


def mape(real, pred):
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    if np.any(real == 0):
        return float("nan")
    return float(np.mean(np.abs((real - pred) / real)) * 100)


def r2_score(real, pred):
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    ss_res = np.sum((real - pred) ** 2)
    ss_tot = np.sum((real - real.mean()) ** 2)
    if ss_tot == 0:
        return float("nan")
    return float(1 - ss_res / ss_tot)


def r2_ajustado(r2, n, n_predictores):
    gl = n - n_predictores - 1
    if gl <= 0:
        return float("nan")
    return float(1 - (1 - r2) * (n - 1) / gl)


# ============================================================
# CARGA
# ============================================================

def cargar_dengue_nacional():

    df = pd.read_csv(DENGUE_SEMANAL)
    df = df.sort_values("semana_epidemiologica").reset_index(drop=True)
    return df


def cargar_dataset_integrado():

    df = pd.read_csv(DATASET_INTEGRADO)
    return df


# ============================================================
# EXPERIMENTO A - PERSISTENCIA
# ============================================================

def experimento_a(df):
    """
    Baseline naive: predice que la proxima semana repite el ultimo valor
    observado. Se evalua en todas las transiciones disponibles.
    """

    semanas = df["semana_epidemiologica"].to_numpy()
    casos = df["casos_dengue"].to_numpy(dtype=float)

    filas = []
    errores = []
    for i in range(1, len(casos)):
        real = casos[i]
        pred = casos[i - 1]
        error = real - pred
        errores.append(error)
        filas.append({
            "semana_objetivo": int(semanas[i]),
            "valor_real": real,
            "prediccion_persistencia": pred,
            "error": error,
            "error_abs": abs(error),
            "error_cuadratico": error ** 2,
        })

    detalle = pd.DataFrame(filas)
    detalle.to_csv(
        os.path.join(OUTPUT_DIR, "expA_persistencia_nacional.csv"),
        index=False
    )

    resumen = {
        "experimento": "A_persistencia_nacional",
        "unidad": "nacional_semanal",
        "semanas_evaluadas": len(errores),
        "mae": mae(casos[1:], casos[:-1]),
        "rmse": rmse(casos[1:], casos[:-1]),
        "mape": mape(casos[1:], casos[:-1]),
        "nota": "Serie nacional provisional; no es la unidad municipio-semana del producto.",
    }

    print("\n========== EXPERIMENTO A: PERSISTENCIA ==========")
    print("Transiciones evaluadas:", len(errores))
    print("MAE  :", round(resumen["mae"], 3))
    print("RMSE :", round(resumen["rmse"], 3))
    print("MAPE :", round(resumen["mape"], 3), "%")

    return resumen


# ============================================================
# EXPERIMENTO B - MODELOS NACIONALES WALK-FORWARD
# ============================================================

def _ols(design, objetivo):
    coef, _, _, _ = np.linalg.lstsq(design, objetivo, rcond=None)
    return coef


def _pred_ols(coef, design):
    return design @ coef


def experimento_b(df):
    """
    Comparacion justa en el mismo conjunto de objetivos, con ventana
    expansiva: media historica, tendencia lineal y AR(1).
    """

    semanas = df["semana_epidemiologica"].to_numpy()
    casos = df["casos_dengue"].to_numpy(dtype=float)

    filas = []

    for k in range(VENTANA_INICIAL, len(casos)):
        entrenamiento = casos[:k]
        t_entrenamiento = np.arange(k, dtype=float)
        real = casos[k]
        t_objetivo = float(k)

        pred_media = float(entrenamiento.mean())

        design_tendencia = np.column_stack(
            [np.ones(k), t_entrenamiento]
        )
        coef_tendencia = _ols(design_tendencia, entrenamiento)
        pred_tendencia = float(_pred_ols(
            coef_tendencia,
            np.array([1.0, t_objetivo])
        ))

        pares_x = entrenamiento[:-1]
        pares_y = entrenamiento[1:]
        design_ar = np.column_stack([np.ones(len(pares_x)), pares_x])
        coef_ar = _ols(design_ar, pares_y)
        pred_ar = float(coef_ar[0] + coef_ar[1] * entrenamiento[-1])

        pred_persistencia = float(entrenamiento[-1])

        filas.append({
            "semana_objetivo": int(semanas[k]),
            "valor_real": real,
            "pred_persistencia": pred_persistencia,
            "pred_media_expansiva": pred_media,
            "pred_tendencia_lineal": pred_tendencia,
            "pred_ar1": pred_ar,
        })

    detalle = pd.DataFrame(filas)
    detalle.to_csv(
        os.path.join(OUTPUT_DIR, "expB_modelos_nacional.csv"),
        index=False
    )

    modelos = {
        "persistencia": "pred_persistencia",
        "media_expansiva": "pred_media_expansiva",
        "tendencia_lineal": "pred_tendencia_lineal",
        "ar1": "pred_ar1",
    }

    filas_resumen = []
    for nombre, columna in modelos.items():
        filas_resumen.append({
            "modelo": nombre,
            "objetivos_evaluados": len(detalle),
            "mae": mae(detalle["valor_real"], detalle[columna]),
            "rmse": rmse(detalle["valor_real"], detalle[columna]),
            "mape": mape(detalle["valor_real"], detalle[columna]),
        })

    resumen_df = pd.DataFrame(filas_resumen).sort_values("mae").reset_index(drop=True)
    resumen_df.to_csv(
        os.path.join(OUTPUT_DIR, "expB_resumen_modelos.csv"),
        index=False
    )

    print("\n========== EXPERIMENTO B: MODELOS WALK-FORWARD ==========")
    print(resumen_df.to_string(index=False))

    mejor = resumen_df.iloc[0]
    resumen = {
        "experimento": "B_modelos_nacional",
        "ventana_inicial_semanas": VENTANA_INICIAL,
        "objetivos_evaluados": len(detalle),
        "resultados": resumen_df.to_dict(orient="records"),
        "mejor_modelo_por_mae": mejor["modelo"],
        "mejor_mae": float(mejor["mae"]),
        "nota": "Walk-forward de un paso; serie nacional provisional, no municipio-semana.",
    }

    return detalle, resumen


# ============================================================
# EXPERIMENTO C - REGRESION CROSS-SECTIONAL
# ============================================================

def _cross_sectional(df, enfermedad, columna_objetivo, disponibles):

    sub = df[df[disponibles]].copy()
    sub = sub.dropna(subset=[columna_objetivo])

    features = [
        "temperatura_media_periodo",
        "humedad_media_periodo",
        "precipitacion_media_dia_observado",
    ]

    x = sub[features].to_numpy(dtype=float)
    y = sub[columna_objetivo].to_numpy(dtype=float)
    n = len(y)

    modelos = {
        "media": [],
        "temperatura": [0],
        "completo_temp_hum_precip": [0, 1, 2],
    }

    filas = []
    for nombre, indices in modelos.items():
        n_predictores = len(indices)
        columnas = [x[:, j] for j in indices]
        design = np.column_stack([np.ones(n)] + columnas) if columnas \
            else np.ones((n, 1))
        n_params = design.shape[1]

        coef = _ols(design, y)
        pred = _pred_ols(coef, design)
        r2 = r2_score(y, pred)
        r2_aj = r2_ajustado(r2, n, n_predictores)

        loocv_valido = (n - 1) > n_params
        loocv_pred = []
        loocv_mae = float("nan")
        if loocv_valido:
            for i in range(n):
                mask = np.ones(n, dtype=bool)
                mask[i] = False
                coef_i = _ols(design[mask], y[mask])
                loocv_pred.append(float(_pred_ols(coef_i, design[i:i + 1])[0]))
            loocv_mae = mae(y, loocv_pred)

        filas.append({
            "enfermedad": enfermedad,
            "modelo": nombre,
            "n": n,
            "n_parametros": n_params,
            "grados_libertad_residual": n - n_params,
            "r2": r2,
            "r2_ajustado": r2_aj,
            "loocv_valido": loocv_valido,
            "loocv_mae": loocv_mae,
            "observaciones": "; ".join(sub["municipio"].tolist()),
        })

    return filas


def experimento_c(df):

    filas = []
    filas += _cross_sectional(
        df, "dengue", "casos_dengue_acumulados_se1_13", "dengue_disponible"
    )
    filas += _cross_sectional(
        df, "malaria", "total_malaria", "malaria_disponible"
    )

    detalle = pd.DataFrame(filas)
    detalle.to_csv(
        os.path.join(OUTPUT_DIR, "expC_cross_sectional.csv"),
        index=False
    )

    print("\n========== EXPERIMENTO C: REGRESION CROSS-SECTIONAL ==========")
    print(detalle[[
        "enfermedad", "modelo", "n", "n_parametros",
        "grados_libertad_residual", "r2", "loocv_valido", "loocv_mae"
    ]].to_string(index=False))

    resumen = {
        "experimento": "C_cross_sectional",
        "filas": detalle.to_dict(orient="records"),
        "nota": (
            "n=4 (dengue) y n=3 (malaria). El modelo con 3 predictores queda "
            "sin grados de libertad (ajuste perfecto, no generalizable); LOOCV "
            "solo es valido cuando n-1 > n_params. Se registra como evidencia "
            "de que la muestra actual no permite un modelo defendible."
        ),
    }

    return resumen


# ============================================================
# EXPERIMENTO D - PROTOCOLO
# ============================================================

def experimento_d():

    protocolo = {
        "experimento": "D_protocolo_baseline",
        "unidad_de_prediccion": "municipio + semana_epidemiologica",
        "objetivo": "casos semanales de dengue/malaria por municipio",
        "baselines_a_superar": [
            "persistencia (ultimo valor observado)",
            "media historica por municipio",
            "naive estacional (misma semana del anio anterior)",
            "clasificador por umbral climatico (regla, no aprendido)",
            "clase mayoritaria / aleatorio (para clasificacion de brote)",
        ],
        "metricas_regresion": ["MAE", "RMSE", "MAPE"],
        "metricas_clasificacion": ["precision", "recall", "F1", "ROC-AUC"],
        "metricas_producto": {
            "NFR-001": "precision espacial >= 75% en zona piloto",
            "NFR-002": "anticipacion minima de 2 semanas",
        },
        "validacion": (
            "split temporal / walk-forward; nunca split aleatorio, para evitar "
            "fuga de informacion entre semanas"
        ),
        "requisito_minimo_de_datos": (
            "serie municipio-semana de casos (al menos ~1 anio por municipio) "
            "para entrenar y validar; hoy no existe (solo acumulados SE1-13)"
        ),
        "estado": "pendiente de datos; la referencia numerica actual es solo nacional (exp A y B)",
    }

    with open(
        os.path.join(OUTPUT_DIR, "protocolo_baseline.json"),
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(protocolo, archivo, ensure_ascii=False, indent=2)

    print("\n========== EXPERIMENTO D: PROTOCOLO ==========")
    print("Unidad objetivo:", protocolo["unidad_de_prediccion"])
    print("Estado:", protocolo["estado"])

    return protocolo


# ============================================================
# GRAFICO
# ============================================================

def grafico_nacional(df, detalle_b):

    semanas = df["semana_epidemiologica"].to_numpy()
    casos = df["casos_dengue"].to_numpy(dtype=float)

    plt.figure(figsize=(10, 5))
    plt.plot(semanas, casos, marker="o", label="Casos reales")

    objetivo = detalle_b["semana_objetivo"].to_numpy()
    plt.plot(
        objetivo,
        detalle_b["pred_persistencia"].to_numpy(),
        marker="s",
        linestyle="--",
        label="Persistencia"
    )
    plt.plot(
        objetivo,
        detalle_b["pred_tendencia_lineal"].to_numpy(),
        marker="^",
        linestyle=":",
        label="Tendencia lineal"
    )

    plt.title(
        "Linea base nacional - Dengue Bolivia SE1-SE13, 2026\n"
        "Walk-forward con ventana inicial de 5 semanas"
    )
    plt.xlabel("Semana epidemiologica")
    plt.ylabel("Casos nacionales")
    plt.xticks(semanas)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, "linea_base_nacional.png"),
        dpi=300
    )
    plt.close()


# ============================================================
# GRAFICOS ADICIONALES DE LECTURA
# ============================================================

def grafico_persistencia(df):
    """
    Experimento A: serie real vs prediccion de persistencia (repite la
    semana anterior). Permite ver el rezago de una semana y los saltos.
    """

    semanas = df["semana_epidemiologica"].to_numpy()
    casos = df["casos_dengue"].to_numpy(dtype=float)

    plt.figure(figsize=(10, 5))
    plt.plot(semanas, casos, marker="o", label="Casos reales")
    plt.plot(
        semanas[1:], casos[:-1],
        marker="s", linestyle="--", color="tab:orange",
        label="Persistencia (y(t-1))",
    )
    plt.title(
        "Experimento A - Persistencia: la prediccion repite la semana anterior\n"
        "Dengue Bolivia SE1-SE13, 2026 (12 transiciones)"
    )
    plt.xlabel("Semana epidemiologica")
    plt.ylabel("Casos nacionales")
    plt.xticks(semanas)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, "expA_persistencia_nacional.png"),
        dpi=300
    )
    plt.close()


def grafico_comparacion_modelos(resumen_b):
    """
    Experimento B: barras de MAE, RMSE y MAPE para los 4 modelos
    walk-forward, resaltando el mejor por MAE.
    """

    filas = resumen_b["resultados"]
    nombres = [f["modelo"] for f in filas]
    metricas = {
        "MAE": [f["mae"] for f in filas],
        "RMSE": [f["rmse"] for f in filas],
        "MAPE (%)": [f["mape"] for f in filas],
    }
    mejor = resumen_b["mejor_modelo_por_mae"]

    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    for eje, (nombre, valores) in zip(ejes, metricas.items()):
        colores = [
            "#d62728" if (nombre == "MAE" and n == mejor) else "#4682B4"
            for n in nombres
        ]
        eje.bar(nombres, valores, color=colores)
        eje.set_title(nombre)
        eje.tick_params(axis="x", rotation=15)
        eje.grid(axis="y", alpha=0.3)
        for i, v in enumerate(valores):
            eje.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    fig.suptitle(
        "Experimento B - Modelos nacionales walk-forward (8 objetivos)\n"
        "Rojo en MAE = mejor modelo. Todos superan 80% de MAPE: sin senal explotable"
    )
    fig.tight_layout()
    fig.savefig(
        os.path.join(OUTPUT_DIR, "expB_comparacion_modelos.png"),
        dpi=300
    )
    plt.close(fig)


def grafico_inviabilidad_cross_sectional(filas):
    """
    Experimento C: R2 y R2 ajustado por modelo, con grados de libertad y
    validez de LOOCV, para evidenciar por que el modelo municipal no es
    defendible con n=4 y n=3.
    """

    etiquetas = {
        "media": "Media",
        "temperatura": "Solo temperatura",
        "completo_temp_hum_precip": "Temp+Humed+Precip",
    }
    orden = list(etiquetas.keys())

    fig, ejes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, enf in zip(ejes, ["dengue", "malaria"]):
        sub = [f for f in filas if f["enfermedad"] == enf]
        sub = sorted(sub, key=lambda f: orden.index(f["modelo"]))
        nombres = [etiquetas[f["modelo"]] for f in sub]
        x = np.arange(len(nombres))
        r2 = [f["r2"] for f in sub]
        r2aj = [f.get("r2_ajustado") for f in sub]
        r2aj = [v if v == v else float("nan") for v in r2aj]

        ax.bar(x - 0.18, r2, 0.36, label="R2", color="#4682B4")
        ax.bar(x + 0.18, r2aj, 0.36, label="R2 ajustado", color="#2ca02c")
        ax.set_xticks(x)
        ax.set_xticklabels(nombres, rotation=15)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_ylim(-1.3, 1.2)
        ax.set_title("{0} (n={1})".format(enf.upper(), sub[0]["n"]))
        ax.grid(axis="y", alpha=0.3)
        for i, f in enumerate(sub):
            loocv = "LOOCV valido" if f["loocv_valido"] else "LOOCV invalido"
            ax.annotate(
                "gl = {0:+.0f}\n{1}".format(
                    f["grados_libertad_residual"], loocv
                ),
                xy=(i, -1.15),
                ha="center",
                va="top",
                fontsize=7,
                color="#333",
            )
    fig.suptitle(
        "Experimento C - Regresion cross-sectional: clima del periodo -> casos acumulados\n"
        "R2 = 1.0 con 0/-1 grados de libertad es sobreajuste sin capacidad de generalizar"
    )
    fig.legend(loc="lower center", ncol=2, frameon=False)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(
        os.path.join(OUTPUT_DIR, "expC_inviabilidad_municipal.png"),
        dpi=300
    )
    plt.close(fig)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nLINEA BASE - PASO 3")
    print("Referencia inicial y registro de experimentos")

    dengue = cargar_dengue_nacional()
    integrado = cargar_dataset_integrado()

    resumen_a = experimento_a(dengue)
    detalle_b, resumen_b = experimento_b(dengue)
    resumen_c = experimento_c(integrado)
    protocolo_d = experimento_d()

    grafico_nacional(dengue, detalle_b)
    grafico_persistencia(dengue)
    grafico_comparacion_modelos(resumen_b)
    grafico_inviabilidad_cross_sectional(resumen_c["filas"])

    resumen = {
        "experimento_a": resumen_a,
        "experimento_b": resumen_b,
        "experimento_c": resumen_c,
        "experimento_d": protocolo_d,
        "entradas": {
            "dengue_semanal": "data/processed/dengue_semanal_validado.csv",
            "dataset_integrado": "data/processed/dataset_integrado_municipal.csv",
        },
        "salidas": [
            "expA_persistencia_nacional.csv",
            "expA_persistencia_nacional.png",
            "expB_modelos_nacional.csv",
            "expB_resumen_modelos.csv",
            "expB_comparacion_modelos.png",
            "expC_cross_sectional.csv",
            "expC_inviabilidad_municipal.png",
            "protocolo_baseline.json",
            "resumen_baseline.json",
            "linea_base_nacional.png",
        ],
    }

    with open(
        os.path.join(OUTPUT_DIR, "resumen_baseline.json"),
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2)

    print("\nLinea base completada.")
    print("Resultados en:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
