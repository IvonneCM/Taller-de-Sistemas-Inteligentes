"""
EDA INTEGRADO AVANZADO
CLIMA + DENGUE + MALARIA
============================================

Proyecto:
Predicción temprana de dengue y malaria en Bolivia.

Fuentes:
- Ministerio de Salud y Deportes de Bolivia
- SENAMHI Bolivia - WIS 2.0

Unidad de análisis actual:
Municipio.

"""

import os
import numpy as np
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
# UTILIDADES
# ============================================================

def guardar_figura(nombre):

    ruta = os.path.join(
        OUTPUT_DIR,
        nombre
    )

    plt.tight_layout()

    plt.savefig(
        ruta,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def crear_heatmap(
    matriz,
    titulo,
    nombre_archivo,
    formato=".2f"
):

    fig, ax = plt.subplots(
        figsize=(11, 8)
    )

    matriz_visual = matriz.astype(float)

    imagen = ax.imshow(
        matriz_visual.values,
        aspect="auto"
    )

    ax.set_xticks(
        range(len(matriz_visual.columns))
    )

    ax.set_xticklabels(
        matriz_visual.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticks(
        range(len(matriz_visual.index))
    )

    ax.set_yticklabels(
        matriz_visual.index
    )

    ax.set_title(
        titulo
    )

    plt.colorbar(
        imagen,
        ax=ax
    )

    for i in range(
        len(matriz_visual.index)
    ):

        for j in range(
            len(matriz_visual.columns)
        ):

            valor = matriz_visual.iloc[
                i,
                j
            ]

            if pd.notna(valor):

                ax.text(
                    j,
                    i,
                    format(
                        valor,
                        formato
                    ),
                    ha="center",
                    va="center",
                    fontsize=8
                )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUTPUT_DIR,
            nombre_archivo
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# CARGA DE DATOS
# ============================================================

def cargar_datos():

    print(
        "\nCargando dataset integrado..."
    )

    if not os.path.exists(DATA_FILE):

        raise FileNotFoundError(
            "No se encontró:\n"
            + DATA_FILE
            + "\nEjecuta primero scripts/integrar_datos.py"
        )

    df = pd.read_csv(
        DATA_FILE
    )

    print(
        "✓ Dataset cargado"
    )

    print(
        "Filas:",
        len(df)
    )

    print(
        "Columnas:",
        len(df.columns)
    )

    return df


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

def informacion_general(df):

    print(
        "\n========== INFORMACIÓN GENERAL =========="
    )

    print(
        "\nMunicipios:"
    )

    for municipio in df[
        "municipio"
    ].tolist():

        print(
            "-",
            municipio
        )

    print(
        "\nMunicipios analizados:",
        len(df)
    )

    if "periodo_clima" in df.columns:

        periodos = (
            df["periodo_clima"]
            .dropna()
            .unique()
        )

        if len(periodos) > 0:

            print(
                "\nPeríodo climático:",
                periodos[0]
            )

    print(
        "Período epidemiológico: SE1-13 2026"
    )

    if (
        "alineacion_temporal_completa"
        in df.columns
    ):

        print(
            "\nAlineación temporal completa:",
            df[
                "alineacion_temporal_completa"
            ].all()
        )

    else:

        print(
            "\nAlineación temporal completa: False"
        )


# ============================================================
# CALIDAD
# ============================================================

def calidad_datos(df):

    print(
        "\n========== CALIDAD DE DATOS =========="
    )

    faltantes = (
        df.isnull()
        .sum()
    )

    faltantes = faltantes[
        faltantes > 0
    ]

    if len(faltantes) == 0:

        print(
            "\nNo existen valores faltantes."
        )

    else:

        print(
            "\nValores faltantes:"
        )

        print(
            faltantes.sort_values(
                ascending=False
            )
        )

    print(
        "\nDuplicados exactos:",
        df.duplicated().sum()
    )

    columnas = [
        "municipio",
        "porcentaje_dias_temperatura",
        "porcentaje_dias_humedad",
        "porcentaje_dias_precipitacion",
        "porcentaje_semanas_cobertura_suficiente",
        "cobertura_climatica_alta"
    ]

    columnas = [
        c
        for c in columnas
        if c in df.columns
    ]

    print(
        "\nCobertura climática:"
    )

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

    if (
        "casos_dengue_acumulados_se1_13"
        in df.columns
    ):

        columnas = [
            "municipio",
            "casos_dengue_acumulados_se1_13"
        ]

        if (
            "incidencia_por_10000_hab"
            in df.columns
        ):

            columnas.append(
                "incidencia_por_10000_hab"
            )

        dengue = (
            df[columnas]
            .sort_values(
                "casos_dengue_acumulados_se1_13",
                ascending=False
            )
        )

        print(
            "\nDengue acumulado SE1-SE13:"
        )

        print(
            dengue.to_string(
                index=False
            )
        )

    if "total_malaria" in df.columns:

        columnas = [
            "municipio"
        ]

        for columna in [
            "p_vivax",
            "p_falciparum",
            "mixta",
            "total_malaria"
        ]:

            if columna in df.columns:

                columnas.append(
                    columna
                )

        malaria = (
            df[columnas]
            .sort_values(
                "total_malaria",
                ascending=False
            )
        )

        print(
            "\nMalaria acumulada SE1-SE13:"
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

    columnas = [
        c
        for c in columnas
        if c in df.columns
    ]

    print(
        df[columnas].to_string(
            index=False
        )
    )


# ============================================================
# TABLA INTEGRADA
# ============================================================

def tabla_integrada(df):

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

    columnas = [
        c
        for c in columnas
        if c in df.columns
    ]

    resumen = df[
        columnas
    ].copy()

    print(
        resumen.to_string(
            index=False
        )
    )

    ruta = os.path.join(
        OUTPUT_DIR,
        "resumen_integrado.csv"
    )

    resumen.to_csv(
        ruta,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\n✓ Tabla guardada:",
        ruta
    )


# ============================================================
# GRÁFICOS BÁSICOS
# ============================================================

def grafico_barras(
    df,
    variable,
    ylabel,
    titulo,
    archivo
):

    if variable not in df.columns:
        return

    datos = (
        df[
            ["municipio", variable]
        ]
        .dropna()
        .sort_values(
            variable,
            ascending=False
        )
    )

    plt.figure(
        figsize=(9, 6)
    )

    plt.bar(
        datos["municipio"],
        datos[variable]
    )

    plt.title(
        titulo
    )

    plt.ylabel(
        ylabel
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    guardar_figura(
        archivo
    )


def graficos_basicos(df):

    print(
        "\n========== GENERANDO GRÁFICOS BÁSICOS =========="
    )

    grafico_barras(
        df,
        "casos_dengue_acumulados_se1_13",
        "Casos",
        "Dengue acumulado por municipio",
        "dengue_por_municipio.png"
    )

    print(
        "✓ Dengue por municipio"
    )

    grafico_barras(
        df,
        "total_malaria",
        "Casos",
        "Malaria acumulada por municipio",
        "malaria_por_municipio.png"
    )

    print(
        "✓ Malaria por municipio"
    )

    grafico_barras(
        df,
        "temperatura_media_periodo",
        "Temperatura media (°C)",
        "Temperatura media por municipio",
        "temperatura_media_municipio.png"
    )

    print(
        "✓ Temperatura media"
    )

    grafico_barras(
        df,
        "humedad_media_periodo",
        "Humedad relativa (%)",
        "Humedad media por municipio",
        "humedad_media_municipio.png"
    )

    print(
        "✓ Humedad media"
    )

    grafico_barras(
        df,
        "precipitacion_media_dia_observado",
        "Precipitación media",
        "Precipitación media por día observado",
        "precipitacion_media_dia.png"
    )

    print(
        "✓ Precipitación"
    )


# ============================================================
# COBERTURA CLIMÁTICA
# ============================================================

def grafico_cobertura(df):

    columnas = [
        "porcentaje_dias_temperatura",
        "porcentaje_dias_humedad",
        "porcentaje_dias_precipitacion"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):
        return

    datos = df.set_index(
        "municipio"
    )[columnas]

    datos.columns = [
        "Temperatura",
        "Humedad",
        "Precipitación"
    ]

    datos.plot(
        kind="bar",
        figsize=(10, 7)
    )

    plt.title(
        "Cobertura climática por municipio"
    )

    plt.ylabel(
        "Cobertura (%)"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.legend(
        title="Variable"
    )

    guardar_figura(
        "cobertura_climatica.png"
    )

    print(
        "✓ Cobertura climática"
    )


# ============================================================
# VARIABLES INTEGRADAS
# ============================================================

def obtener_variables_integradas(df):

    candidatos = {
        "Temperatura":
            "temperatura_media_periodo",

        "Humedad":
            "humedad_media_periodo",

        "Precipitación":
            "precipitacion_media_dia_observado",

        "Dengue":
            "casos_dengue_acumulados_se1_13",

        "Incidencia dengue":
            "incidencia_por_10000_hab",

        "Malaria":
            "total_malaria"
    }

    variables = {}

    for nombre, columna in candidatos.items():

        if columna in df.columns:

            variables[
                nombre
            ] = columna

    return variables


# ============================================================
# CORRELACIONES INTEGRADAS
# ============================================================

def correlaciones_integradas(df):

    print(
        "\n========== CORRELACIONES INTEGRADAS =========="
    )

    variables = (
        obtener_variables_integradas(
            df
        )
    )

    columnas = list(
        variables.values()
    )

    datos = (
        df[columnas]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
    )

    pearson = datos.corr(
        method="pearson",
        min_periods=3
    )

    spearman = datos.corr(
        method="spearman",
        min_periods=3
    )

    nombres = {
        valor: clave
        for clave, valor
        in variables.items()
    }

    pearson = pearson.rename(
        index=nombres,
        columns=nombres
    )

    spearman = spearman.rename(
        index=nombres,
        columns=nombres
    )

    print(
        "\nPearson:"
    )

    print(
        pearson.round(3).to_string()
    )

    print(
        "\nSpearman:"
    )

    print(
        spearman.round(3).to_string()
    )

    pearson.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlacion_integrada_pearson.csv"
        ),
        encoding="utf-8-sig"
    )

    spearman.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlacion_integrada_spearman.csv"
        ),
        encoding="utf-8-sig"
    )

    crear_heatmap(
        pearson,
        "Correlaciones de Pearson\nClima + Epidemiología",
        "heatmap_correlacion_integrada_pearson.png"
    )

    crear_heatmap(
        spearman,
        "Correlaciones de Spearman\nClima + Epidemiología",
        "heatmap_correlacion_integrada_spearman.png"
    )

    print(
        "✓ Heatmaps de correlaciones"
    )


# ============================================================
# CLIMA VS ENFERMEDADES
# ============================================================

def correlaciones_clima_enfermedad(df):

    print(
        "\n========== CLIMA VS ENFERMEDADES =========="
    )

    variables_clima = {
        "Temperatura":
            "temperatura_media_periodo",

        "Humedad":
            "humedad_media_periodo",

        "Precipitación":
            "precipitacion_media_dia_observado"
    }

    enfermedades = {
        "Dengue":
            "casos_dengue_acumulados_se1_13",

        "Incidencia dengue":
            "incidencia_por_10000_hab",

        "Malaria":
            "total_malaria"
    }

    resultados = []

    for nombre_clima, clima in (
        variables_clima.items()
    ):

        if clima not in df.columns:
            continue

        for nombre_enfermedad, enfermedad in (
            enfermedades.items()
        ):

            if enfermedad not in df.columns:
                continue

            datos = (
                df[
                    [clima, enfermedad]
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce"
                )
                .dropna()
            )

            n = len(datos)

            if n >= 3:

                pearson = (
                    datos[clima]
                    .corr(
                        datos[enfermedad],
                        method="pearson"
                    )
                )

                spearman = (
                    datos[clima]
                    .corr(
                        datos[enfermedad],
                        method="spearman"
                    )
                )

            else:

                pearson = np.nan
                spearman = np.nan

            resultados.append({
                "variable_climatica":
                    nombre_clima,

                "variable_epidemiologica":
                    nombre_enfermedad,

                "n":
                    n,

                "pearson":
                    pearson,

                "spearman":
                    spearman
            })

    resultado = pd.DataFrame(
        resultados
    )

    print(
        resultado.round(3).to_string(
            index=False
        )
    )

    resultado.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlaciones_clima_enfermedad.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    matriz = resultado.pivot(
        index="variable_climatica",
        columns="variable_epidemiologica",
        values="spearman"
    )

    crear_heatmap(
        matriz,
        "Asociaciones clima-epidemiología\n"
        "Correlación de Spearman",
        "heatmap_clima_enfermedades.png"
    )

    print(
        "✓ Heatmap clima vs enfermedades"
    )


# ============================================================
# SCATTER GENERAL
# ============================================================

def scatter_integrado(
    df,
    x,
    y,
    xlabel,
    ylabel,
    titulo,
    archivo
):

    columnas = [
        "municipio",
        x,
        y
    ]

    if (
        "cobertura_climatica_alta"
        in df.columns
    ):

        columnas.append(
            "cobertura_climatica_alta"
        )

    datos = df[
        columnas
    ].copy()

    datos[x] = pd.to_numeric(
        datos[x],
        errors="coerce"
    )

    datos[y] = pd.to_numeric(
        datos[y],
        errors="coerce"
    )

    datos = datos.dropna(
        subset=[x, y]
    )

    plt.figure(
        figsize=(9, 7)
    )

    for _, fila in datos.iterrows():

        cobertura = (
            fila[
                "cobertura_climatica_alta"
            ]
            if
            "cobertura_climatica_alta"
            in datos.columns
            else True
        )

        marcador = (
            "o"
            if cobertura
            else "x"
        )

        plt.scatter(
            fila[x],
            fila[y],
            s=120,
            marker=marcador
        )

        plt.annotate(
            fila["municipio"],
            (
                fila[x],
                fila[y]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel(
        xlabel
    )

    plt.ylabel(
        ylabel
    )

    plt.title(
        titulo
        + "\n○ cobertura alta | × cobertura menor"
    )

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        archivo
    )


# ============================================================
# TODOS LOS SCATTERS
# ============================================================

def generar_scatters(df):

    configuraciones = [

        (
            "temperatura_media_periodo",
            "casos_dengue_acumulados_se1_13",
            "Temperatura media (°C)",
            "Casos acumulados de dengue",
            "Temperatura vs dengue",
            "temperatura_vs_dengue.png"
        ),

        (
            "humedad_media_periodo",
            "casos_dengue_acumulados_se1_13",
            "Humedad media (%)",
            "Casos acumulados de dengue",
            "Humedad vs dengue",
            "humedad_vs_dengue.png"
        ),

        (
            "precipitacion_media_dia_observado",
            "casos_dengue_acumulados_se1_13",
            "Precipitación media por día observado",
            "Casos acumulados de dengue",
            "Precipitación vs dengue",
            "precipitacion_vs_dengue.png"
        ),

        (
            "temperatura_media_periodo",
            "incidencia_por_10000_hab",
            "Temperatura media (°C)",
            "Incidencia por 10.000 habitantes",
            "Temperatura vs incidencia de dengue",
            "temperatura_vs_incidencia_dengue.png"
        ),

        (
            "humedad_media_periodo",
            "incidencia_por_10000_hab",
            "Humedad media (%)",
            "Incidencia por 10.000 habitantes",
            "Humedad vs incidencia de dengue",
            "humedad_vs_incidencia_dengue.png"
        ),

        (
            "precipitacion_media_dia_observado",
            "incidencia_por_10000_hab",
            "Precipitación media por día observado",
            "Incidencia por 10.000 habitantes",
            "Precipitación vs incidencia de dengue",
            "precipitacion_vs_incidencia_dengue.png"
        ),

        (
            "temperatura_media_periodo",
            "total_malaria",
            "Temperatura media (°C)",
            "Casos acumulados de malaria",
            "Temperatura vs malaria",
            "temperatura_vs_malaria.png"
        ),

        (
            "humedad_media_periodo",
            "total_malaria",
            "Humedad media (%)",
            "Casos acumulados de malaria",
            "Humedad vs malaria",
            "humedad_vs_malaria.png"
        ),

        (
            "precipitacion_media_dia_observado",
            "total_malaria",
            "Precipitación media por día observado",
            "Casos acumulados de malaria",
            "Precipitación vs malaria",
            "precipitacion_vs_malaria.png"
        )
    ]

    print(
        "\n========== GRÁFICOS DE RELACIONES =========="
    )

    for (
        x,
        y,
        xlabel,
        ylabel,
        titulo,
        archivo
    ) in configuraciones:

        if (
            x in df.columns
            and y in df.columns
        ):

            scatter_integrado(
                df,
                x,
                y,
                xlabel,
                ylabel,
                titulo,
                archivo
            )

            print(
                "✓",
                titulo
            )


# ============================================================
# PERFIL NORMALIZADO
# ============================================================

def perfil_integrado(df):

    print(
        "\n========== PERFIL INTEGRADO =========="
    )

    variables = (
        obtener_variables_integradas(
            df
        )
    )

    columnas = list(
        variables.values()
    )

    matriz = (
        df.set_index(
            "municipio"
        )[columnas]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
    )

    matriz.columns = list(
        variables.keys()
    )

    normalizada = matriz.copy()

    for columna in (
        normalizada.columns
    ):

        media = (
            normalizada[columna]
            .mean()
        )

        std = (
            normalizada[columna]
            .std()
        )

        if (
            pd.notna(std)
            and std > 0
        ):

            normalizada[columna] = (
                normalizada[columna]
                - media
            ) / std

        else:

            normalizada[columna] = 0

    normalizada.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "perfil_integrado_normalizado.csv"
        ),
        encoding="utf-8-sig"
    )

    crear_heatmap(
        normalizada,
        "Perfil relativo clima-epidemiología\n"
        "Valores estandarizados (z-score)",
        "heatmap_perfil_integrado.png"
    )

    print(
        "✓ Perfil integrado normalizado"
    )


# ============================================================
# MULTIVARIABLE DENGUE
# ============================================================

def multivariable_dengue(df):

    columnas = [
        "municipio",
        "temperatura_media_periodo",
        "humedad_media_periodo",
        "casos_dengue_acumulados_se1_13"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):

        return

    datos = (
        df[columnas]
        .copy()
    )

    for columna in columnas[1:]:

        datos[columna] = (
            pd.to_numeric(
                datos[columna],
                errors="coerce"
            )
        )

    datos = datos.dropna()

    dengue = datos[
        "casos_dengue_acumulados_se1_13"
    ]

    maximo = dengue.max()

    if maximo > 0:

        tamanos = (
            100
            + dengue / maximo * 700
        )

    else:

        tamanos = np.repeat(
            100,
            len(datos)
        )

    plt.figure(
        figsize=(10, 7)
    )

    plt.scatter(
        datos[
            "temperatura_media_periodo"
        ],
        datos[
            "humedad_media_periodo"
        ],
        s=tamanos,
        alpha=0.65
    )

    for _, fila in datos.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila[
                    "temperatura_media_periodo"
                ],
                fila[
                    "humedad_media_periodo"
                ]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel(
        "Temperatura media (°C)"
    )

    plt.ylabel(
        "Humedad media (%)"
    )

    plt.title(
        "Perfil climático y dengue\n"
        "Tamaño del punto = casos de dengue"
    )

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        "perfil_climatico_dengue.png"
    )

    print(
        "✓ Perfil climático + dengue"
    )


# ============================================================
# MULTIVARIABLE MALARIA
# ============================================================

def multivariable_malaria(df):

    columnas = [
        "municipio",
        "precipitacion_media_dia_observado",
        "humedad_media_periodo",
        "total_malaria"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):

        return

    datos = (
        df[columnas]
        .copy()
    )

    for columna in columnas[1:]:

        datos[columna] = (
            pd.to_numeric(
                datos[columna],
                errors="coerce"
            )
        )

    datos = datos.dropna()

    malaria = datos[
        "total_malaria"
    ]

    maximo = malaria.max()

    if maximo > 0:

        tamanos = (
            100
            + malaria / maximo * 700
        )

    else:

        tamanos = np.repeat(
            100,
            len(datos)
        )

    plt.figure(
        figsize=(10, 7)
    )

    plt.scatter(
        datos[
            "precipitacion_media_dia_observado"
        ],
        datos[
            "humedad_media_periodo"
        ],
        s=tamanos,
        alpha=0.65
    )

    for _, fila in datos.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila[
                    "precipitacion_media_dia_observado"
                ],
                fila[
                    "humedad_media_periodo"
                ]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel(
        "Precipitación media por día observado"
    )

    plt.ylabel(
        "Humedad media (%)"
    )

    plt.title(
        "Perfil climático y malaria\n"
        "Tamaño del punto = casos de malaria"
    )

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        "perfil_climatico_malaria.png"
    )

    print(
        "✓ Perfil climático + malaria"
    )


# ============================================================
# COBERTURA VS DENGUE
# ============================================================

def cobertura_vs_dengue(df):

    columnas = [
        "municipio",
        "porcentaje_dias_precipitacion",
        "casos_dengue_acumulados_se1_13"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):

        return

    datos = df[
        columnas
    ].dropna()

    plt.figure(
        figsize=(9, 7)
    )

    plt.scatter(
        datos[
            "porcentaje_dias_precipitacion"
        ],
        datos[
            "casos_dengue_acumulados_se1_13"
        ],
        s=120
    )

    for _, fila in datos.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila[
                    "porcentaje_dias_precipitacion"
                ],
                fila[
                    "casos_dengue_acumulados_se1_13"
                ]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel(
        "Cobertura climática (%)"
    )

    plt.ylabel(
        "Casos acumulados de dengue"
    )

    plt.title(
        "Cobertura climática de los municipios analizados"
    )

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        "cobertura_vs_dengue.png"
    )


# ============================================================
# RANKING / PERFIL DE VARIABLES POR MUNICIPIO
# ============================================================

def heatmap_municipios_variables(df):

    variables = (
        obtener_variables_integradas(
            df
        )
    )

    matriz = (
        df.set_index(
            "municipio"
        )[
            list(
                variables.values()
            )
        ]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
    )

    matriz.columns = list(
        variables.keys()
    )

    # Min-Max únicamente para comparación visual.
    visual = matriz.copy()

    for columna in visual.columns:

        minimo = visual[
            columna
        ].min()

        maximo = visual[
            columna
        ].max()

        if (
            pd.notna(maximo)
            and pd.notna(minimo)
            and maximo != minimo
        ):

            visual[columna] = (
                visual[columna]
                - minimo
            ) / (
                maximo
                - minimo
            )

        else:

            visual[columna] = 0

    crear_heatmap(
        visual,
        "Comparación relativa entre municipios\n"
        "0 = menor valor | 1 = mayor valor",
        "heatmap_municipios_variables.png"
    )

    visual.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "comparacion_relativa_municipios.csv"
        ),
        encoding="utf-8-sig"
    )

    print(
        "✓ Comparación relativa por municipio"
    )


# ============================================================
# MALARIA POR ESPECIE
# ============================================================

def composicion_malaria(df):

    columnas = [
        "p_vivax",
        "p_falciparum",
        "mixta"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):

        return

    datos = (
        df.set_index(
            "municipio"
        )[columnas]
        .dropna(
            how="all"
        )
    )

    datos.columns = [
        "P. vivax",
        "P. falciparum",
        "Mixta"
    ]

    datos.plot(
        kind="bar",
        stacked=True,
        figsize=(10, 7)
    )

    plt.title(
        "Composición de casos de malaria por municipio"
    )

    plt.xlabel(
        "Municipio"
    )

    plt.ylabel(
        "Casos"
    )

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.legend(
        title="Tipo"
    )

    guardar_figura(
        "composicion_malaria.png"
    )

    print(
        "✓ Composición de malaria"
    )


# ============================================================
# INCIDENCIA VS CASOS DENGUE
# ============================================================

def casos_vs_incidencia_dengue(df):

    columnas = [
        "municipio",
        "casos_dengue_acumulados_se1_13",
        "incidencia_por_10000_hab"
    ]

    if not all(
        c in df.columns
        for c in columnas
    ):

        return

    datos = df[
        columnas
    ].dropna()

    plt.figure(
        figsize=(9, 7)
    )

    plt.scatter(
        datos[
            "casos_dengue_acumulados_se1_13"
        ],
        datos[
            "incidencia_por_10000_hab"
        ],
        s=120
    )

    for _, fila in datos.iterrows():

        plt.annotate(
            fila["municipio"],
            (
                fila[
                    "casos_dengue_acumulados_se1_13"
                ],
                fila[
                    "incidencia_por_10000_hab"
                ]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel(
        "Casos acumulados de dengue"
    )

    plt.ylabel(
        "Incidencia por 10.000 habitantes"
    )

    plt.title(
        "Casos absolutos vs incidencia de dengue"
    )

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        "casos_vs_incidencia_dengue.png"
    )

    print(
        "✓ Casos vs incidencia de dengue"
    )


# ============================================================
# COMPARACIÓN COBERTURA ALTA / BAJA
# ============================================================

def resumen_cobertura(df):

    if (
        "cobertura_climatica_alta"
        not in df.columns
    ):

        return

    print(
        "\n========== COBERTURA CLIMÁTICA =========="
    )

    alta = df[
        df[
            "cobertura_climatica_alta"
        ] == True
    ]

    baja = df[
        df[
            "cobertura_climatica_alta"
        ] == False
    ]

    print(
        "\nCobertura alta:",
        len(alta),
        "/",
        len(df)
    )

    if len(alta) > 0:

        print(
            alta[
                "municipio"
            ].tolist()
        )

    print(
        "\nCobertura menor:",
        len(baja),
        "/",
        len(df)
    )

    if len(baja) > 0:

        print(
            baja[
                "municipio"
            ].tolist()
        )


# ============================================================
# TABLA FINAL PARA ANÁLISIS
# ============================================================

def guardar_comparacion_final(df):

    columnas = [
        "municipio",
        "temperatura_media_periodo",
        "humedad_media_periodo",
        "precipitacion_media_dia_observado",
        "casos_dengue_acumulados_se1_13",
        "incidencia_por_10000_hab",
        "p_vivax",
        "p_falciparum",
        "mixta",
        "total_malaria",
        "porcentaje_dias_temperatura",
        "porcentaje_dias_humedad",
        "porcentaje_dias_precipitacion",
        "porcentaje_semanas_cobertura_suficiente",
        "cobertura_climatica_alta"
    ]

    columnas = [
        c
        for c in columnas
        if c in df.columns
    ]

    df[
        columnas
    ].to_csv(
        os.path.join(
            OUTPUT_DIR,
            "comparacion_municipios_integrada.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# RESUMEN METODOLÓGICO
# ============================================================

def generar_resumen_metodologico(df):

    n = len(df)

    n_dengue = (
        df[
            "casos_dengue_acumulados_se1_13"
        ]
        .notna()
        .sum()
        if
        "casos_dengue_acumulados_se1_13"
        in df.columns
        else 0
    )

    n_malaria = (
        df[
            "total_malaria"
        ]
        .notna()
        .sum()
        if
        "total_malaria"
        in df.columns
        else 0
    )

    n_alta = (
        int(
            df[
                "cobertura_climatica_alta"
            ].sum()
        )
        if
        "cobertura_climatica_alta"
        in df.columns
        else 0
    )

    texto = f"""
EDA INTEGRADO - CLIMA + DENGUE + MALARIA
=========================================

FUENTES
-------
Clima:
SENAMHI Bolivia - WIS 2.0

Epidemiología:
Ministerio de Salud y Deportes de Bolivia
Boletín Epidemiológico N°13, 2026.

UNIDAD DE ANÁLISIS
------------------
Municipio.

Municipios integrados:
{n}

Municipios con información de dengue:
{n_dengue}

Municipios con información de malaria:
{n_malaria}

Municipios con cobertura climática alta:
{n_alta}

PERÍODOS
--------
Datos climáticos:
SE3-SE13 2026 aproximadamente.

Datos epidemiológicos:
SE1-SE13 2026 acumulados.

La alineación temporal no es completa.

ANÁLISIS REALIZADOS
-------------------
1. Calidad y valores faltantes.
2. Cobertura climática.
3. Resumen epidemiológico.
4. Resumen climático.
5. Correlaciones de Pearson.
6. Correlaciones de Spearman.
7. Relaciones clima-dengue.
8. Relaciones clima-incidencia de dengue.
9. Relaciones clima-malaria.
10. Perfil climático-epidemiológico por municipio.
11. Comparación normalizada entre municipios.
12. Composición de malaria.
13. Análisis de cobertura de las observaciones.

INTERPRETACIÓN
--------------
Los coeficientes de correlación se utilizan únicamente
como herramientas exploratorias para identificar posibles
patrones entre las variables climáticas y epidemiológicas.

Una correlación positiva indica que ambas variables tienden
a variar en la misma dirección.

Una correlación negativa indica que tienden a variar en
direcciones opuestas.

Una correlación cercana a cero indica ausencia de una
relación monotónica o lineal clara dentro de los datos
observados.

IMPORTANTE:
Correlación no implica causalidad.

LIMITACIONES
------------
1. Actualmente solo existen {n} municipios integrados.

2. Para malaria existen únicamente {n_malaria} municipios
   con información coincidente.

3. Una correlación calculada con n=3 o n=4 es extremadamente
   sensible a cada observación individual.

4. Por esta razón, incluso coeficientes cercanos a 1 o -1
   no constituyen evidencia estadística suficiente.

5. La cobertura climática no es homogénea entre municipios.

6. Guayaramerín e Ixiamas presentan mejor cobertura
   climática que Palos Blancos y San Buenaventura.

7. El período climático no coincide completamente con el
   período epidemiológico.

8. Los casos epidemiológicos municipales disponibles son
   acumulados para SE1-SE13, mientras que las variables
   climáticas resumen principalmente SE3-SE13.

9. No es posible establecer relaciones temporales de
   retraso entre clima y enfermedad con el dataset
   municipal acumulado actual.

CONCLUSIÓN METODOLÓGICA
-----------------------
Este EDA permite caracterizar los datos reales disponibles
y explorar posibles asociaciones entre clima, dengue y
malaria.

Los resultados son útiles para formular hipótesis y
determinar qué variables podrían resultar relevantes en
etapas posteriores.

Sin embargo, para construir un modelo de predicción
temprana de 3 a 4 semanas será necesario contar con una
serie epidemiológica temporal más granular, idealmente
municipio-semana, y ampliar la cobertura histórica.

Por tanto, las correlaciones actuales deben considerarse
descriptivas y exploratorias, no como evidencia causal ni
como validación de un modelo predictivo.
"""

    ruta = os.path.join(
        OUTPUT_DIR,
        "resumen_eda_integrado.txt"
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            texto.strip()
        )

    print(
        "\n✓ Resumen metodológico guardado:",
        ruta
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

    # 2. Información básica
    informacion_general(
        df
    )

    # 3. Calidad
    calidad_datos(
        df
    )

    # 4. Epidemiología
    resumen_epidemiologico(
        df
    )

    # 5. Clima
    resumen_climatico(
        df
    )

    # 6. Tabla integrada
    tabla_integrada(
        df
    )

    # 7. Gráficos básicos
    graficos_basicos(
        df
    )

    # 8. Cobertura
    grafico_cobertura(
        df
    )

    # 9. Correlaciones completas
    correlaciones_integradas(
        df
    )

    # 10. Clima vs enfermedades
    correlaciones_clima_enfermedad(
        df
    )

    # 11. Scatters
    generar_scatters(
        df
    )

    # 12. Perfil integrado z-score
    perfil_integrado(
        df
    )

    # 13. Multivariable dengue
    multivariable_dengue(
        df
    )

    # 14. Multivariable malaria
    multivariable_malaria(
        df
    )

    # 15. Cobertura vs dengue
    cobertura_vs_dengue(
        df
    )

    # 16. Comparación relativa
    heatmap_municipios_variables(
        df
    )

    # 17. Composición malaria
    composicion_malaria(
        df
    )

    # 18. Casos vs incidencia
    casos_vs_incidencia_dengue(
        df
    )

    # 19. Resumen cobertura
    resumen_cobertura(
        df
    )

    # 20. Tabla final
    guardar_comparacion_final(
        df
    )

    # 21. Resumen metodológico
    generar_resumen_metodologico(
        df
    )

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