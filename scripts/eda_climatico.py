"""
EDA climático inicial
Sistema de Predicción Temprana de Brotes de Dengue y Malaria

Fuente:
SENAMHI Bolivia - WIS 2.0

Este script analiza únicamente observaciones climáticas reales:
- Temperatura del aire
- Humedad relativa
- Precipitación acumulada en 24 horas

No se generan ni imputan datos sintéticos.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "clima",
    "senamhi",
    "senamhi_raw_SE01_13_2026.csv"
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "eda_climatico_output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# NOMBRES DE VARIABLES
# ============================================================

TEMP = "air_temperature"
HUMEDAD = "relative_humidity"
PRECIP = "total_precipitation_or_total_water_equivalent"


# ============================================================
# CARGA
# ============================================================

def cargar_datos():

    print("\nCargando datos SENAMHI...")

    df = pd.read_csv(DATA_FILE)

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"],
        utc=True
    )

    df["valor"] = pd.to_numeric(
        df["valor"],
        errors="coerce"
    )

    print("✓ Datos cargados:", len(df))

    return df


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

def informacion_general(df):

    print("\n========== INFORMACIÓN GENERAL ==========")

    print("Filas:", len(df))
    print("Columnas:", len(df.columns))

    print(
        "Desde:",
        df["fecha_hora"].min()
    )

    print(
        "Hasta:",
        df["fecha_hora"].max()
    )

    print("\nRegistros por municipio:")
    print(df["municipio"].value_counts())

    print("\nRegistros por variable:")
    print(df["variable"].value_counts())


# ============================================================
# CALIDAD DE DATOS
# ============================================================

def analizar_calidad(df):

    print("\n========== CALIDAD DE DATOS ==========")

    faltantes = int(
        df.isnull().sum().sum()
    )

    duplicados = int(
        df.duplicated().sum()
    )

    print("Valores faltantes:", faltantes)
    print("Duplicados exactos:", duplicados)

    resumen = []

    for municipio in sorted(
        df["municipio"].dropna().unique()
    ):

        datos = df[
            df["municipio"] == municipio
        ]

        resumen.append({
            "municipio": municipio,
            "registros": len(datos),
            "fecha_inicio": datos["fecha_hora"].min(),
            "fecha_fin": datos["fecha_hora"].max(),
            "faltantes": int(
                datos.isnull().sum().sum()
            ),
            "duplicados": int(
                datos.duplicated().sum()
            )
        })

    calidad = pd.DataFrame(resumen)

    calidad.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "calidad_climatica.csv"
        ),
        index=False
    )

    print("\nCobertura por municipio:")
    print(calidad.to_string(index=False))


# ============================================================
# RESUMEN ESTADÍSTICO
# ============================================================

def generar_resumen(df):

    resumen = (
        df.groupby(
            ["municipio", "variable"]
        )["valor"]
        .agg([
            "count",
            "mean",
            "median",
            "std",
            "min",
            "max"
        ])
        .reset_index()
    )

    resumen.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resumen_climatico.csv"
        ),
        index=False
    )

    print("\n========== RESUMEN CLIMÁTICO ==========")
    print(resumen.to_string(index=False))


# ============================================================
# OUTLIERS IQR
# ============================================================

def detectar_outliers_grupo(datos):

    if len(datos) < 4:
        return datos.iloc[0:0]

    q1 = datos["valor"].quantile(0.25)
    q3 = datos["valor"].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    return datos[
        (datos["valor"] < limite_inferior) |
        (datos["valor"] > limite_superior)
    ]


def analizar_outliers(df):

    resultados = []

    for municipio in df["municipio"].unique():

        for variable in df["variable"].unique():

            datos = df[
                (df["municipio"] == municipio) &
                (df["variable"] == variable)
            ].copy()

            if datos.empty:
                continue

            outliers = detectar_outliers_grupo(
                datos
            )

            resultados.append({
                "municipio": municipio,
                "variable": variable,
                "registros": len(datos),
                "outliers": len(outliers),
                "porcentaje_outliers": round(
                    len(outliers) /
                    len(datos) * 100,
                    2
                )
            })

    resumen = pd.DataFrame(resultados)

    resumen.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "outliers_climaticos.csv"
        ),
        index=False
    )

    print("\n========== OUTLIERS ==========")
    print(resumen.to_string(index=False))


# ============================================================
# DISTRIBUCIONES
# ============================================================

def grafico_distribucion(
    df,
    variable,
    titulo,
    xlabel,
    archivo
):

    datos = df[
        df["variable"] == variable
    ]["valor"].dropna()

    plt.figure(figsize=(9, 5))

    plt.hist(
        datos,
        bins=30,
        edgecolor="black"
    )

    plt.title(titulo)
    plt.xlabel(xlabel)
    plt.ylabel("Frecuencia")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            archivo
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# BOXPLOTS POR MUNICIPIO
# ============================================================

def grafico_boxplot(
    df,
    variable,
    titulo,
    ylabel,
    archivo
):

    municipios = sorted(
        df["municipio"].unique()
    )

    datos = []

    etiquetas = []

    for municipio in municipios:

        valores = df[
            (df["municipio"] == municipio) &
            (df["variable"] == variable)
        ]["valor"].dropna()

        if not valores.empty:
            datos.append(valores)
            etiquetas.append(municipio)

    plt.figure(figsize=(10, 6))

    plt.boxplot(
        datos,
        tick_labels=etiquetas
    )

    plt.title(titulo)
    plt.ylabel(ylabel)

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            archivo
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# SERIES TEMPORALES DIARIAS
# ============================================================

def serie_diaria(
    df,
    variable,
    titulo,
    ylabel,
    archivo,
    metodo="mean"
):

    datos = df[
        df["variable"] == variable
    ].copy()

    datos["fecha"] = (
        datos["fecha_hora"]
        .dt.floor("D")
    )

    if metodo == "sum":

        diario = (
            datos.groupby(
                ["municipio", "fecha"]
            )["valor"]
            .sum()
            .reset_index()
        )

    else:

        diario = (
            datos.groupby(
                ["municipio", "fecha"]
            )["valor"]
            .mean()
            .reset_index()
        )

    plt.figure(figsize=(12, 6))

    for municipio in sorted(
        diario["municipio"].unique()
    ):

        subset = diario[
            diario["municipio"] == municipio
        ]

        plt.plot(
            subset["fecha"],
            subset["valor"],
            label=municipio
        )

    plt.title(titulo)
    plt.xlabel("Fecha")
    plt.ylabel(ylabel)

    plt.legend()

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            archivo
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# COBERTURA DE OBSERVACIONES
# ============================================================

def analizar_cobertura(df):

    cobertura = (
        df.groupby(
            ["municipio", "variable"]
        )
        .agg(
            registros=("valor", "count"),
            fecha_inicio=("fecha_hora", "min"),
            fecha_fin=("fecha_hora", "max")
        )
        .reset_index()
    )

    cobertura.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "cobertura_observaciones.csv"
        ),
        index=False
    )


# ============================================================
# PRECIPITACIÓN
# ============================================================

def analizar_precipitacion(df):

    lluvia = df[
        df["variable"] == PRECIP
    ].copy()

    if lluvia.empty:
        print(
            "\nNo existen registros de precipitación."
        )
        return

    # Cada registro conservado por el descargador
    # corresponde a precipitación acumulada en 24 h.

    resumen = (
        lluvia.groupby("municipio")["valor"]
        .agg([
            "count",
            "mean",
            "median",
            "max"
        ])
        .reset_index()
    )

    resumen = resumen.rename(
        columns={
            "count": "observaciones_24h",
            "mean": "precipitacion_media_24h",
            "median": "precipitacion_mediana_24h",
            "max": "precipitacion_maxima_24h"
        }
    )

    resumen.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resumen_precipitacion.csv"
        ),
        index=False
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "EDA CLIMÁTICO - SENAMHI"
    )

    print(
        "=========================================="
    )

    print(
        "Fuente: SENAMHI Bolivia - WIS 2.0"
    )

    df = cargar_datos()

    informacion_general(df)

    analizar_calidad(df)

    generar_resumen(df)

    analizar_outliers(df)

    analizar_cobertura(df)

    analizar_precipitacion(df)


    # --------------------------------------------------------
    # DISTRIBUCIONES
    # --------------------------------------------------------

    grafico_distribucion(
        df,
        TEMP,
        "Distribución de temperatura del aire",
        "Temperatura (°C)",
        "distribucion_temperatura.png"
    )

    grafico_distribucion(
        df,
        HUMEDAD,
        "Distribución de humedad relativa",
        "Humedad relativa (%)",
        "distribucion_humedad.png"
    )

    grafico_distribucion(
        df,
        PRECIP,
        "Distribución de precipitación acumulada en 24 horas",
        "Precipitación (mm)",
        "distribucion_precipitacion.png"
    )


    # --------------------------------------------------------
    # BOXPLOTS
    # --------------------------------------------------------

    grafico_boxplot(
        df,
        TEMP,
        "Temperatura por estación meteorológica",
        "Temperatura (°C)",
        "boxplot_temperatura.png"
    )

    grafico_boxplot(
        df,
        HUMEDAD,
        "Humedad relativa por estación meteorológica",
        "Humedad (%)",
        "boxplot_humedad.png"
    )

    grafico_boxplot(
        df,
        PRECIP,
        "Precipitación 24 h por estación meteorológica",
        "Precipitación (mm)",
        "boxplot_precipitacion.png"
    )


    # --------------------------------------------------------
    # SERIES TEMPORALES
    # --------------------------------------------------------

    serie_diaria(
        df,
        TEMP,
        "Temperatura media diaria por estación",
        "Temperatura (°C)",
        "serie_temporal_temperatura.png"
    )

    serie_diaria(
        df,
        HUMEDAD,
        "Humedad relativa media diaria por estación",
        "Humedad relativa (%)",
        "serie_temporal_humedad.png"
    )

    # IMPORTANTE:
    # Para precipitación NO sumamos todas las observaciones
    # intradía porque cada una representa una ventana móvil de
    # 24 horas y eso produciría doble conteo.
    # Mostramos el promedio de las observaciones 24 h del día.

    serie_diaria(
        df,
        PRECIP,
        "Precipitación 24 h reportada por estación",
        "Precipitación (mm)",
        "serie_temporal_precipitacion.png",
        metodo="mean"
    )


    print(
        "\n=========================================="
    )

    print(
        "✓ EDA CLIMÁTICO COMPLETADO"
    )

    print(
        "=========================================="
    )

    print(
        "\nResultados guardados en:"
    )

    print(
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()