"""
EDA inicial — Sistema de Predicción Temprana de Brotes de Dengue/Malaria
Tarea: Adriana Rocha — Análisis exploratorio de datos (EDA) inicial

IMPORTANTE: no se cuenta todavía con acceso confirmado a los datos reales de
SENAMHI ni de SEDES (ver docs/priorizacion_casos.md). Este script genera un
dataset SINTÉTICO que replica las características documentadas de ambas
fuentes (volumen, formato, gaps geográficos, sesgo de vigilancia) para dejar
el pipeline de perfilado listo y reproducible. Al llegar los datos reales,
basta con reemplazar las funciones `generar_datos_climaticos_sinteticos()` y
`generar_datos_epidemiologicos_sinteticos()` por los conectores de ingesta
reales (ver design.md, app/etl/conectores/).

Uso:
    python eda_inicial.py

Salida:
    - docs/eda_output/resumen_climatico.csv
    - docs/eda_output/resumen_epidemiologico.csv
    - docs/eda_output/outliers_climaticos.csv
    - docs/eda_output/faltantes_por_municipio.png
    - docs/eda_output/distribucion_variables.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs_eda_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Municipios de ejemplo (La Paz — zona piloto sugerida, pendiente confirmación oficial)
MUNICIPIOS = [
    "La Paz", "El Alto", "Coroico", "Caranavi", "Rurrenabaque",
    "Palos Blancos", "Guanay", "Apolo", "Ixiamas", "San Buenaventura",
]

# Municipios rurales con menor densidad de estaciones (ver design.md — cobertura
# irregular) y menor reporte epidemiológico (sesgo de vigilancia)
MUNICIPIOS_RURALES = ["Apolo", "Ixiamas", "Guanay", "San Buenaventura"]

FECHA_INICIO = "2024-01-01"
FECHA_FIN = "2026-08-31"


def generar_datos_climaticos_sinteticos() -> pd.DataFrame:
    """Simula datos_climaticos con la estructura de design.md §3, imitando
    la cobertura irregular de estaciones SENAMHI en zonas rurales."""
    fechas = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="D")
    filas = []
    for municipio in MUNICIPIOS:
        es_rural = municipio in MUNICIPIOS_RURALES
        # Zonas rurales: menor densidad de estaciones -> más huecos de reporte
        prob_faltante = 0.25 if es_rural else 0.03
        for fecha in fechas:
            if np.random.random() < prob_faltante:
                continue  # día sin registro (estación no reportó)
            temp = np.random.normal(24, 3)
            humedad = np.clip(np.random.normal(70, 12), 0, 100)
            precip = max(0, np.random.exponential(4))
            # outliers ocasionales (posibles errores de sensor)
            if np.random.random() < 0.005:
                temp += np.random.choice([-15, 20])
            filas.append({
                "municipio": municipio,
                "fecha": fecha,
                "temperatura_media_c": round(temp, 1),
                "humedad_relativa_pct": round(humedad, 1),
                "precipitacion_mm": round(precip, 1),
                "fuente": "SENAMHI",
            })
    return pd.DataFrame(filas)


def generar_datos_epidemiologicos_sinteticos() -> pd.DataFrame:
    """Simula casos_epidemiologicos con la estructura de design.md §3,
    imitando el retraso de reporte y sesgo de vigilancia de SEDES."""
    fechas = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="W")
    filas = []
    for municipio in MUNICIPIOS:
        es_rural = municipio in MUNICIPIOS_RURALES
        # Sesgo de vigilancia: zonas rurales reportan menos, no porque haya
        # menos casos reales, sino por menor infraestructura de salud
        factor_reporte = 0.4 if es_rural else 1.0
        base_casos = np.random.uniform(2, 15)
        for fecha in fechas:
            estacionalidad = 1 + 0.6 * np.sin(2 * np.pi * fecha.dayofyear / 365)
            casos = max(0, np.random.poisson(base_casos * estacionalidad * factor_reporte))
            filas.append({
                "municipio": municipio,
                "enfermedad": np.random.choice(["dengue", "malaria"], p=[0.75, 0.25]),
                "fecha_reporte": fecha,
                "casos_confirmados": casos,
                "fuente": "SEDES La Paz",
            })
    return pd.DataFrame(filas)


def perfilar_faltantes(df_clima: pd.DataFrame) -> pd.DataFrame:
    """Calcula, por municipio, el % de días sin registro climático dentro
    de la ventana total — soporta NFR-007 (tolerancia a datos incompletos)."""
    dias_totales = (pd.Timestamp(FECHA_FIN) - pd.Timestamp(FECHA_INICIO)).days + 1
    conteo = df_clima.groupby("municipio").size()
    faltantes_pct = (1 - conteo / dias_totales) * 100
    resumen = faltantes_pct.reset_index()
    resumen.columns = ["municipio", "pct_dias_faltantes"]
    return resumen.sort_values("pct_dias_faltantes", ascending=False)


def detectar_outliers_iqr(df_clima: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Detección de outliers por rango intercuartílico (IQR), por variable."""
    q1, q3 = df_clima[columna].quantile([0.25, 0.75])
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return df_clima[(df_clima[columna] < lim_inf) | (df_clima[columna] > lim_sup)]


def graficar_faltantes(resumen_faltantes: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    plt.barh(resumen_faltantes["municipio"], resumen_faltantes["pct_dias_faltantes"])
    plt.xlabel("% de días sin registro climático")
    plt.title("Cobertura de datos climáticos por municipio (SENAMHI, sintético)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "faltantes_por_municipio.png"))
    plt.close()


def graficar_distribuciones(df_clima: pd.DataFrame, df_epi: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].hist(df_clima["temperatura_media_c"], bins=30)
    axes[0].set_title("Temperatura media (°C)")
    axes[1].hist(df_clima["precipitacion_mm"], bins=30)
    axes[1].set_title("Precipitación (mm)")
    axes[2].hist(df_epi["casos_confirmados"], bins=30)
    axes[2].set_title("Casos confirmados por semana")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "distribucion_variables.png"))
    plt.close()


def main():
    df_clima = generar_datos_climaticos_sinteticos()
    df_epi = generar_datos_epidemiologicos_sinteticos()

    print(f"Registros climáticos generados: {len(df_clima)}")
    print(f"Registros epidemiológicos generados: {len(df_epi)}")
    print(f"Rango de fechas: {FECHA_INICIO} a {FECHA_FIN}")

    resumen_clima = df_clima.describe(include="all")
    resumen_epi = df_epi.describe(include="all")
    resumen_clima.to_csv(os.path.join(OUTPUT_DIR, "resumen_climatico.csv"))
    resumen_epi.to_csv(os.path.join(OUTPUT_DIR, "resumen_epidemiologico.csv"))

    faltantes = perfilar_faltantes(df_clima)
    print("\nCobertura de datos climáticos por municipio (top faltantes):")
    print(faltantes.head())

    outliers_temp = detectar_outliers_iqr(df_clima, "temperatura_media_c")
    outliers_temp.to_csv(os.path.join(OUTPUT_DIR, "outliers_climaticos.csv"), index=False)
    print(f"\nOutliers de temperatura detectados (IQR): {len(outliers_temp)}")

    graficar_faltantes(faltantes)
    graficar_distribuciones(df_clima, df_epi)

    print(f"\nArchivos de salida guardados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()