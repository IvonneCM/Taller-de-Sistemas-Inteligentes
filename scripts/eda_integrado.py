"""
EDA INTEGRADO - CLIMA + DENGUE + MALARIA

Proyecto:
Predicción temprana de brotes de Dengue y Malaria

Fuentes:
- SENAMHI Bolivia - WIS 2.0
- Ministerio de Salud y Deportes de Bolivia

IMPORTANTE:
- Clima disponible: SE3-SE13 de 2026.
- Epidemiología: acumulados municipales SE1-SE13 de 2026.
- Solo existen 4 municipios en la integración.
- El análisis es descriptivo y exploratorio.
- No se interpretan asociaciones como causalidad.
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

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "dataset_integrado_municipal.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "scripts",
    "eda_integrado_output"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# CARGAR DATOS
# ============================================================

def cargar_datos():

    print("\nCargando dataset integrado...")

    df = pd.read_csv(INPUT_FILE)

    print("✓ Dataset cargado")
    print("Filas:", len(df))
    print("Columnas:", len(df.columns))

    return df


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

def informacion_general(df):

    print(
        "\n========== INFORMACIÓN GENERAL =========="
    )

    print("\nMunicipios:")

    for municipio in df["municipio"]:
        print("-", municipio)

    print(
        "\nMunicipios analizados:",
        df["municipio"].nunique()
    )

    print(
        "\nPeríodo climático:",
        df["periodo_clima"].iloc[0]
    )

    print(
        "Período epidemiológico:",
        df["periodo_epidemiologia"].iloc[0]
    )

    print(
        "\nAlineación temporal completa:",
        df["alineacion_temporal_completa"].iloc[0]
    )


# ============================================================
# CALIDAD DE DATOS
# ============================================================

def calidad_datos(df):

    print(
        "\n========== CALIDAD DE DATOS =========="
    )

    faltantes = (
        df.isnull()
        .sum()
        .sort_values(ascending=False)
    )

    faltantes = faltantes[
        faltantes > 0
    ]

    if faltantes.empty:

        print(
            "No existen valores faltantes."
        )

    else:

        print(
            "\nValores faltantes:"
        )

        print(faltantes)


    duplicados = df.duplicated().sum()

    print(
        "\nDuplicados exactos:",
        duplicados
    )


    print(
        "\nCobertura climática:"
    )

    columnas = [
        "municipio",
        "porcentaje_dias_temperatura",
        "porcentaje_dias_humedad",
        "porcentaje_dias_precipitacion",
        "porcentaje_semanas_cobertura_suficiente",
        "cobertura_climatica_alta"
    ]

    print(
        df[columnas].to_string(
            index=False
        )
    )


# ============================================================
# RESUMEN EPIDEMIOLÓGICO
# ============================================================

def resumen_epidemiologico(df):

    print(
        "\n========== RESUMEN EPIDEMIOLÓGICO =========="
    )


    # --------------------------------------------------------
    # DENGUE
    # --------------------------------------------------------

    print(
        "\nDengue acumulado SE1-SE13:"
    )

    dengue = df[
        [
            "municipio",
            "casos_dengue_acumulados_se1_13",
            "incidencia_por_10000_hab"
        ]
    ].sort_values(
        "casos_dengue_acumulados_se1_13",
        ascending=False
    )

    print(
        dengue.to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # MALARIA
    # --------------------------------------------------------

    print(
        "\nMalaria acumulada SE1-SE13:"
    )

    malaria = df[
        [
            "municipio",
            "p_vivax",
            "p_falciparum",
            "mixta",
            "total_malaria"
        ]
    ].sort_values(
        "total_malaria",
        ascending=False,
        na_position="last"
    )

    print(
        malaria.to_string(
            index=False
        )
    )


# ============================================================
# RESUMEN CLIMÁTICO
# ============================================================

def resumen_climatico(df):

    print(
        "\n========== RESUMEN CLIMÁTICO =========="
    )

    columnas = [
        "municipio",
        "temperatura_media_periodo",
        "humedad_media_periodo",
        "precipitacion_total_periodo_mm",
        "precipitacion_media_dia_observado",
        "porcentaje_dias_precipitacion",
        "cobertura_climatica_alta"
    ]

    print(
        df[columnas]
        .sort_values(
            "municipio"
        )
        .to_string(
            index=False
        )
    )


# ============================================================
# TABLA RESUMEN
# ============================================================

def crear_tabla_resumen(df):

    print(
        "\n========== TABLA INTEGRADA =========="
    )

    columnas = [
        "municipio",
        "temperatura_media_periodo",
        "humedad_media_periodo",
        "precipitacion_media_dia_observado",
        "casos_dengue_acumulados_se1_13",
        "incidencia_por_10000_hab",
        "total_malaria",
        "porcentaje_dias_precipitacion",
        "cobertura_climatica_alta"
    ]

    resumen = df[columnas].copy()

    archivo = os.path.join(
        OUTPUT_DIR,
        "resumen_integrado.csv"
    )

    resumen.to_csv(
        archivo,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        resumen.to_string(
            index=False
        )
    )

    print(
        "\n✓ Tabla guardada:",
        archivo
    )


# ============================================================
# GRÁFICO 1 - DENGUE
# ============================================================

def grafico_dengue(df):

    datos = df.sort_values(
        "casos_dengue_acumulados_se1_13",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[
            "casos_dengue_acumulados_se1_13"
        ]
    )

    plt.title(
        "Casos acumulados de dengue por municipio\nSE1-SE13 de 2026"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Casos acumulados"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "dengue_por_municipio.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 2 - MALARIA
# ============================================================

def grafico_malaria(df):

    datos = df[
        df["total_malaria"].notna()
    ].copy()

    datos = datos.sort_values(
        "total_malaria",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos["total_malaria"]
    )

    plt.title(
        "Casos acumulados de malaria por municipio\nSE1-SE13 de 2026"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Casos acumulados"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "malaria_por_municipio.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 3 - TEMPERATURA
# ============================================================

def grafico_temperatura(df):

    datos = df.sort_values(
        "temperatura_media_periodo",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[
            "temperatura_media_periodo"
        ]
    )

    plt.title(
        "Temperatura media por municipio\nClima disponible SE3-SE13 de 2026"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Temperatura media (°C)"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "temperatura_media_municipio.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 4 - HUMEDAD
# ============================================================

def grafico_humedad(df):

    datos = df.sort_values(
        "humedad_media_periodo",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[
            "humedad_media_periodo"
        ]
    )

    plt.title(
        "Humedad relativa media por municipio\nClima disponible SE3-SE13 de 2026"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Humedad relativa media (%)"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "humedad_media_municipio.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 5 - PRECIPITACIÓN NORMALIZADA
# ============================================================

def grafico_precipitacion(df):

    datos = df.sort_values(
        "precipitacion_media_dia_observado",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[
            "precipitacion_media_dia_observado"
        ]
    )

    plt.title(
        "Precipitación media por día observado\nClima disponible SE3-SE13 de 2026"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Precipitación media (mm/día observado)"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "precipitacion_media_dia.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 6 - COBERTURA
# ============================================================

def grafico_cobertura(df):

    datos = df.sort_values(
        "porcentaje_dias_precipitacion",
        ascending=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[
            "porcentaje_dias_precipitacion"
        ]
    )

    plt.axhline(
        y=80,
        linestyle="--",
        label="Umbral de cobertura alta (80%)"
    )

    plt.title(
        "Cobertura de observaciones climáticas por municipio"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Días con observación (%)"
    )

    plt.ylim(
        0,
        105
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.legend()

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "cobertura_climatica.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 7 - CLIMA VS DENGUE
# ============================================================

def grafico_clima_dengue(df):

    # Este gráfico es únicamente exploratorio.
    # No implica correlación significativa ni causalidad.

    plt.figure(
        figsize=(8, 6)
    )

    plt.scatter(
        df["temperatura_media_periodo"],
        df[
            "casos_dengue_acumulados_se1_13"
        ],
        s=80
    )

    for _, fila in df.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila["temperatura_media_periodo"],
                fila[
                    "casos_dengue_acumulados_se1_13"
                ]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.title(
        "Temperatura media y casos acumulados de dengue\nAnálisis exploratorio"
    )

    plt.xlabel(
        "Temperatura media (°C)"
    )

    plt.ylabel(
        "Casos acumulados de dengue"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "temperatura_vs_dengue.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# GRÁFICO 8 - CLIMA VS MALARIA
# ============================================================

def grafico_clima_malaria(df):

    # Palos Blancos tiene malaria ausente (NaN).
    # No se convierte a cero.

    datos = df[
        df["total_malaria"].notna()
    ].copy()

    plt.figure(
        figsize=(8, 6)
    )

    plt.scatter(
        datos[
            "precipitacion_media_dia_observado"
        ],
        datos["total_malaria"],
        s=80
    )

    for _, fila in datos.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila[
                    "precipitacion_media_dia_observado"
                ],
                fila["total_malaria"]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.title(
        "Precipitación y casos acumulados de malaria\nAnálisis exploratorio"
    )

    plt.xlabel(
        "Precipitación media (mm/día observado)"
    )

    plt.ylabel(
        "Casos acumulados de malaria"
    )

    plt.tight_layout()

    archivo = os.path.join(
        OUTPUT_DIR,
        "precipitacion_vs_malaria.png"
    )

    plt.savefig(
        archivo,
        dpi=300
    )

    plt.close()


# ============================================================
# RESUMEN DEL EDA
# ============================================================

def generar_resumen(df):

    archivo = os.path.join(
        OUTPUT_DIR,
        "resumen_eda_integrado.txt"
    )

    cobertura_alta = int(
        df["cobertura_climatica_alta"].sum()
    )

    dengue_disponible = int(
        df[
            "casos_dengue_acumulados_se1_13"
        ].notna().sum()
    )

    malaria_disponible = int(
        df[
            "total_malaria"
        ].notna().sum()
    )

    contenido = f"""
EDA INTEGRADO - CLIMA + DENGUE + MALARIA
========================================

FUENTES
-------
SENAMHI Bolivia - WIS 2.0
Ministerio de Salud y Deportes de Bolivia

COBERTURA
---------
Municipios integrados: {len(df)}
Municipios con dengue disponible: {dengue_disponible}
Municipios con malaria disponible: {malaria_disponible}
Municipios con cobertura climática alta: {cobertura_alta}

PERÍODOS
--------
Clima disponible: SE3-SE13 de 2026
Epidemiología: SE1-SE13 de 2026

LIMITACIONES
------------
1. La cobertura temporal de las fuentes no coincide completamente.

2. Los datos epidemiológicos municipales corresponden a
   acumulados SE1-SE13 y no a observaciones semanales.

3. Los datos climáticos utilizados corresponden a SE3-SE13.

4. Palos Blancos no tiene registro de malaria en el dataset
   utilizado. La ausencia se conserva como dato faltante y
   no se interpreta como cero casos.

5. Palos Blancos y San Buenaventura presentan menor cobertura
   de observaciones climáticas.

6. El dataset integrado contiene únicamente cuatro municipios.

7. Por el tamaño de la muestra no se realizan inferencias
   estadísticas fuertes ni se interpretan asociaciones
   exploratorias como relaciones causales.

8. Este dataset se utiliza para EDA e integración de fuentes.
   No constituye por sí solo un dataset suficiente para
   entrenar un modelo predictivo de brotes.

CONCLUSIÓN METODOLÓGICA
-----------------------
La integración permite comparar descriptivamente variables
climáticas y epidemiológicas en los municipios con información
coincidente. Sin embargo, será necesario ampliar la cobertura
temporal y epidemiológica para construir posteriormente un
modelo de predicción temprana de brotes.
"""

    with open(
        archivo,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            contenido.strip()
        )

    print(
        "\n✓ Resumen metodológico guardado:",
        archivo
    )


# ============================================================
# GENERAR GRÁFICOS
# ============================================================

def generar_graficos(df):

    print(
        "\n========== GENERANDO GRÁFICOS =========="
    )

    grafico_dengue(df)

    print(
        "✓ Dengue por municipio"
    )

    grafico_malaria(df)

    print(
        "✓ Malaria por municipio"
    )

    grafico_temperatura(df)

    print(
        "✓ Temperatura media"
    )

    grafico_humedad(df)

    print(
        "✓ Humedad media"
    )

    grafico_precipitacion(df)

    print(
        "✓ Precipitación"
    )

    grafico_cobertura(df)

    print(
        "✓ Cobertura climática"
    )

    grafico_clima_dengue(df)

    print(
        "✓ Temperatura vs dengue"
    )

    grafico_clima_malaria(df)

    print(
        "✓ Precipitación vs malaria"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "EDA INTEGRADO - CLIMA + DENGUE + MALARIA"
    )

    print(
        "=========================================="
    )

    # 1. Cargar
    df = cargar_datos()

    # 2. Información general
    informacion_general(df)

    # 3. Calidad
    calidad_datos(df)

    # 4. Epidemiología
    resumen_epidemiologico(df)

    # 5. Clima
    resumen_climatico(df)

    # 6. Tabla integrada
    crear_tabla_resumen(df)

    # 7. Gráficos
    generar_graficos(df)

    # 8. Resumen metodológico
    generar_resumen(df)

    print(
        "\n=========================================="
    )

    print(
        "✓ EDA INTEGRADO COMPLETADO"
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