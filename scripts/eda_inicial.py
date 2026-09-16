"""
EDA epidemiológico inicial
Sistema de Predicción Temprana de Brotes de Dengue y Malaria

Responsable: Adriana Rocha

Fuente:
Ministerio de Salud y Deportes de Bolivia
Boletín Epidemiológico N° 13 - 2026

IMPORTANTE:
Este análisis utiliza únicamente datos epidemiológicos reales.
No se generan datos sintéticos.

El análisis climático con SENAMHI se realizará posteriormente.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "epidemiologia"
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "eda_output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


DENGUE_SEMANAL = os.path.join(
    DATA_DIR,
    "dengue_bolivia_semanal_SE01_13_2026.csv"
)

DENGUE_MUNICIPAL = os.path.join(
    DATA_DIR,
    "dengue_bolivia_municipal_SE01_13_2026.csv"
)

MALARIA_MUNICIPAL = os.path.join(
    DATA_DIR,
    "malaria_bolivia_municipal_SE01_13_2026.csv"
)


# ============================================================
# CARGA
# ============================================================

def cargar_datos():

    dengue_semanal = pd.read_csv(DENGUE_SEMANAL)
    dengue_municipal = pd.read_csv(DENGUE_MUNICIPAL)
    malaria = pd.read_csv(MALARIA_MUNICIPAL)

    return dengue_semanal, dengue_municipal, malaria


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_datos(dengue_semanal, dengue_municipal, malaria):

    print("\n========== VALIDACIÓN ==========")

    total_dengue = dengue_semanal["casos_dengue"].sum()

    total_dengue_municipal = (
        dengue_municipal[
            "casos_dengue_acumulados_se1_13"
        ].sum()
    )

    total_malaria = malaria["total_malaria"].sum()

    print("Dengue semanal:", total_dengue)
    print("Dengue municipal:", total_dengue_municipal)
    print("Malaria:", total_malaria)

    # Totales reportados por el boletín
    assert total_dengue == 341, \
        "ERROR: dengue semanal no suma 341"

    assert total_dengue_municipal == 341, \
        "ERROR: dengue municipal no suma 341"

    assert total_malaria == 1615, \
        "ERROR: malaria no suma 1615"

    print("\n✓ Los totales coinciden con el boletín oficial.")


# ============================================================
# CALIDAD DE DATOS
# ============================================================

def analizar_calidad(dengue_semanal, dengue_municipal, malaria):

    resultados = []

    datasets = {
        "Dengue semanal": dengue_semanal,
        "Dengue municipal": dengue_municipal,
        "Malaria municipal": malaria
    }

    for nombre, df in datasets.items():

        resultados.append({
            "dataset": nombre,
            "filas": len(df),
            "columnas": len(df.columns),
            "valores_faltantes": int(df.isnull().sum().sum()),
            "duplicados": int(df.duplicated().sum())
        })

    calidad = pd.DataFrame(resultados)

    calidad.to_csv(
        os.path.join(OUTPUT_DIR, "calidad_datos.csv"),
        index=False
    )

    print("\n========== CALIDAD DE DATOS ==========")
    print(calidad.to_string(index=False))


# ============================================================
# ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

def generar_resumenes(
    dengue_semanal,
    dengue_municipal,
    malaria
):

    dengue_semanal.describe().to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resumen_dengue_semanal.csv"
        )
    )

    dengue_municipal.describe().to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resumen_dengue_municipal.csv"
        )
    )

    malaria.describe().to_csv(
        os.path.join(
            OUTPUT_DIR,
            "resumen_malaria.csv"
        )
    )


# ============================================================
# OUTLIERS CON IQR
# ============================================================

def detectar_outliers(df, columna):

    q1 = df[columna].quantile(0.25)
    q3 = df[columna].quantile(0.75)

    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    return df[
        (df[columna] < limite_inferior) |
        (df[columna] > limite_superior)
    ]


def analizar_outliers(dengue_municipal, malaria):

    outliers_dengue = detectar_outliers(
        dengue_municipal,
        "casos_dengue_acumulados_se1_13"
    )

    outliers_malaria = detectar_outliers(
        malaria,
        "total_malaria"
    )

    outliers_dengue.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "outliers_dengue.csv"
        ),
        index=False
    )

    outliers_malaria.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "outliers_malaria.csv"
        ),
        index=False
    )

    print("\n========== OUTLIERS ==========")

    print(
        "Municipios atípicos dengue:",
        len(outliers_dengue)
    )

    print(
        "Municipios atípicos malaria:",
        len(outliers_malaria)
    )


# ============================================================
# SERIE TEMPORAL DENGUE
# ============================================================

def grafico_dengue_semanal(df):

    plt.figure(figsize=(10, 5))

    plt.plot(
        df["semana_epidemiologica"],
        df["casos_dengue"],
        marker="o"
    )

    plt.title(
        "Casos de dengue por semana epidemiológica\n"
        "Bolivia - SE 1 a SE 13, 2026"
    )

    plt.xlabel("Semana epidemiológica")
    plt.ylabel("Casos reportados")

    plt.xticks(
        df["semana_epidemiologica"]
    )

    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "dengue_serie_temporal.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# DENGUE POR MUNICIPIO
# ============================================================

def grafico_dengue_municipio(df):

    datos = df.sort_values(
        "casos_dengue_acumulados_se1_13",
        ascending=True
    )

    plt.figure(figsize=(10, 9))

    plt.barh(
        datos["municipio"],
        datos["casos_dengue_acumulados_se1_13"]
    )

    plt.title(
        "Casos acumulados de dengue por municipio\n"
        "SE 1-13, Bolivia 2026"
    )

    plt.xlabel("Casos acumulados")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "dengue_por_municipio.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# MALARIA POR MUNICIPIO
# ============================================================

def grafico_malaria_municipio(df):

    datos = df.sort_values(
        "total_malaria",
        ascending=True
    )

    plt.figure(figsize=(10, 8))

    plt.barh(
        datos["municipio"],
        datos["total_malaria"]
    )

    plt.title(
        "Casos acumulados de malaria por municipio\n"
        "SE 1-13, Bolivia 2026"
    )

    plt.xlabel("Casos acumulados")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "malaria_por_municipio.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# MALARIA POR ESPECIE
# ============================================================

def grafico_malaria_especie(df):

    especies = {
        "P. vivax": df["p_vivax"].sum(),
        "P. falciparum": df["p_falciparum"].sum(),
        "Mixta": df["mixta"].sum()
    }

    plt.figure(figsize=(8, 5))

    plt.bar(
        especies.keys(),
        especies.values()
    )

    plt.title(
        "Casos de malaria según especie\n"
        "Bolivia - SE 1-13, 2026"
    )

    plt.ylabel("Número de casos")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "malaria_por_especie.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# DISTRIBUCIONES
# ============================================================

def grafico_distribuciones(
    dengue_municipal,
    malaria
):

    plt.figure(figsize=(8, 5))

    plt.hist(
        dengue_municipal[
            "casos_dengue_acumulados_se1_13"
        ],
        bins=10,
        edgecolor="black"
    )

    plt.title(
        "Distribución de casos de dengue por municipio"
    )

    plt.xlabel("Casos acumulados")
    plt.ylabel("Número de municipios")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "distribucion_dengue.png"
        ),
        dpi=300
    )

    plt.close()


    plt.figure(figsize=(8, 5))

    plt.hist(
        malaria["total_malaria"],
        bins=10,
        edgecolor="black"
    )

    plt.title(
        "Distribución de casos de malaria por municipio"
    )

    plt.xlabel("Casos acumulados")
    plt.ylabel("Número de municipios")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "distribucion_malaria.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nEDA EPIDEMIOLÓGICO - DENGUE Y MALARIA"
    )

    print(
        "Fuente: Ministerio de Salud y Deportes "
        "de Bolivia - Boletín N°13, 2026"
    )

    dengue_semanal, dengue_municipal, malaria = (
        cargar_datos()
    )

    validar_datos(
        dengue_semanal,
        dengue_municipal,
        malaria
    )

    analizar_calidad(
        dengue_semanal,
        dengue_municipal,
        malaria
    )

    generar_resumenes(
        dengue_semanal,
        dengue_municipal,
        malaria
    )

    analizar_outliers(
        dengue_municipal,
        malaria
    )

    grafico_dengue_semanal(
        dengue_semanal
    )

    grafico_dengue_municipio(
        dengue_municipal
    )

    grafico_malaria_municipio(
        malaria
    )

    grafico_malaria_especie(
        malaria
    )

    grafico_distribuciones(
        dengue_municipal,
        malaria
    )

    print(
        "\n✓ EDA completado."
    )

    print(
        "Resultados guardados en:",
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()