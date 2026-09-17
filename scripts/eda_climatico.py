"""
EDA CLIMÁTICO AVANZADO - SENAMHI BOLIVIA
=========================================

Variables:
- Temperatura
- Humedad relativa
- Precipitación

Nivel principal de análisis:
Municipio - Semana epidemiológica

Fuente:
SENAMHI Bolivia - WIS 2.0

Objetivos:
- Analizar calidad y cobertura.
- Estudiar evolución temporal.
- Analizar relaciones entre variables climáticas.
- Detectar patrones municipales.
- Detectar semanas climáticamente extremas.
- Generar visualizaciones interpretativas.

IMPORTANTE:
Las correlaciones son asociaciones exploratorias.
No implican causalidad.
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

SEMANAL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "clima_semanal.csv"
)

DIARIO_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "clima_diario.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "scripts",
    "eda_climatico_output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def heatmap(
    matriz,
    titulo,
    xlabel,
    ylabel,
    nombre_archivo,
    formato=".2f"
):

    fig, ax = plt.subplots(
        figsize=(10, 7)
    )

    imagen = ax.imshow(
        matriz.values,
        aspect="auto"
    )

    ax.set_xticks(
        range(len(matriz.columns))
    )

    ax.set_xticklabels(
        matriz.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticks(
        range(len(matriz.index))
    )

    ax.set_yticklabels(
        matriz.index
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_title(titulo)

    plt.colorbar(
        imagen,
        ax=ax
    )

    # Valores dentro de las celdas
    for i in range(len(matriz.index)):

        for j in range(len(matriz.columns)):

            valor = matriz.iloc[i, j]

            if pd.notna(valor):

                ax.text(
                    j,
                    i,
                    format(valor, formato),
                    ha="center",
                    va="center",
                    fontsize=8
                )

    guardar_figura(
        nombre_archivo
    )


# ============================================================
# CARGAR DATOS
# ============================================================

def cargar_datos():

    print("\nCargando datasets climáticos...")

    semanal = pd.read_csv(
        SEMANAL_FILE
    )

    diario = pd.read_csv(
        DIARIO_FILE
    )

    print(
        "✓ Semanal:",
        len(semanal),
        "registros"
    )

    print(
        "✓ Diario:",
        len(diario),
        "registros"
    )

    print(
        "\nColumnas dataset semanal:"
    )

    print(
        semanal.columns.tolist()
    )

    return semanal, diario


# ============================================================
# DETECTAR COLUMNAS
# ============================================================

def detectar_columnas(df):

    columnas = df.columns.tolist()

    def buscar(palabras):

        for columna in columnas:

            nombre = columna.lower()

            if all(
                palabra in nombre
                for palabra in palabras
            ):

                return columna

        return None

    temperatura = buscar(
        ["temperatura", "media"]
    )

    humedad = buscar(
        ["humedad", "media"]
    )

    precipitacion = buscar(
        ["precipitacion", "total"]
    )

    if precipitacion is None:

        precipitacion = buscar(
            ["precipitacion"]
        )

    print(
        "\nVariables detectadas:"
    )

    print(
        "Temperatura:",
        temperatura
    )

    print(
        "Humedad:",
        humedad
    )

    print(
        "Precipitación:",
        precipitacion
    )

    if (
        temperatura is None
        or humedad is None
        or precipitacion is None
    ):

        raise ValueError(
            "No se pudieron detectar las variables "
            "climáticas principales."
        )

    return (
        temperatura,
        humedad,
        precipitacion
    )


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

def informacion_general(df):

    print(
        "\n========== INFORMACIÓN GENERAL =========="
    )

    print(
        "Registros:",
        len(df)
    )

    print(
        "Municipios:",
        df["municipio"].nunique()
    )

    print(
        "Semanas:",
        df[
            "semana_epidemiologica"
        ].nunique()
    )

    print(
        "\nMunicipios:"
    )

    for municipio in sorted(
        df["municipio"].unique()
    ):

        print(
            "-",
            municipio
        )


# ============================================================
# CALIDAD Y COBERTURA
# ============================================================

def calidad_datos(df):

    print(
        "\n========== CALIDAD =========="
    )

    print(
        "Valores faltantes:",
        df.isnull().sum().sum()
    )

    print(
        "Duplicados:",
        df.duplicated().sum()
    )

    columnas_cobertura = [
        columna
        for columna in [
            "municipio",
            "semana_epidemiologica",
            "dias_con_temperatura",
            "dias_con_humedad",
            "dias_con_precipitacion",
            "cobertura_suficiente"
        ]
        if columna in df.columns
    ]

    cobertura = df[
        columnas_cobertura
    ].copy()

    cobertura.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "cobertura_semanal.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

def estadisticas_descriptivas(
    df,
    temperatura,
    humedad,
    precipitacion
):

    print(
        "\n========== ESTADÍSTICAS DESCRIPTIVAS =========="
    )

    variables = [
        temperatura,
        humedad,
        precipitacion
    ]

    resumen = (
        df[
            variables
        ]
        .describe()
        .T
    )

    print(
        resumen.to_string()
    )

    resumen.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "estadisticas_climaticas.csv"
        ),
        encoding="utf-8-sig"
    )


# ============================================================
# CORRELACIONES GENERALES
# ============================================================

def correlaciones(
    df,
    temperatura,
    humedad,
    precipitacion
):

    print(
        "\n========== CORRELACIONES =========="
    )

    variables = [
        temperatura,
        humedad,
        precipitacion
    ]

    datos = df[
        variables
    ].copy()

    pearson = datos.corr(
        method="pearson"
    )

    spearman = datos.corr(
        method="spearman"
    )

    print(
        "\nPearson:"
    )

    print(
        pearson.round(3)
    )

    print(
        "\nSpearman:"
    )

    print(
        spearman.round(3)
    )

    pearson.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlacion_pearson.csv"
        ),
        encoding="utf-8-sig"
    )

    spearman.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlacion_spearman.csv"
        ),
        encoding="utf-8-sig"
    )

    nombres = {
        temperatura: "Temperatura",
        humedad: "Humedad",
        precipitacion: "Precipitación"
    }

    pearson_visual = pearson.rename(
        index=nombres,
        columns=nombres
    )

    spearman_visual = spearman.rename(
        index=nombres,
        columns=nombres
    )

    heatmap(
        pearson_visual,
        "Correlación climática de Pearson\nMunicipio-semana",
        "Variable",
        "Variable",
        "heatmap_correlacion_pearson.png"
    )

    heatmap(
        spearman_visual,
        "Correlación climática de Spearman\nMunicipio-semana",
        "Variable",
        "Variable",
        "heatmap_correlacion_spearman.png"
    )


# ============================================================
# CORRELACIONES POR MUNICIPIO
# ============================================================

def correlaciones_por_municipio(
    df,
    temperatura,
    humedad,
    precipitacion
):

    resultados = []

    for municipio, grupo in df.groupby(
        "municipio"
    ):

        variables = grupo[
            [
                temperatura,
                humedad,
                precipitacion
            ]
        ]

        correlacion = variables.corr(
            method="spearman"
        )

        resultados.append({
            "municipio": municipio,

            "temp_humedad":
                correlacion.loc[
                    temperatura,
                    humedad
                ],

            "temp_precipitacion":
                correlacion.loc[
                    temperatura,
                    precipitacion
                ],

            "humedad_precipitacion":
                correlacion.loc[
                    humedad,
                    precipitacion
                ]
        })

    resultado = pd.DataFrame(
        resultados
    )

    print(
        "\n========== CORRELACIONES POR MUNICIPIO =========="
    )

    print(
        resultado.round(3).to_string(
            index=False
        )
    )

    resultado.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "correlaciones_por_municipio.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    matriz = resultado.set_index(
        "municipio"
    )

    matriz.columns = [
        "Temp-Humedad",
        "Temp-Precipitación",
        "Humedad-Precipitación"
    ]

    heatmap(
        matriz,
        "Relaciones climáticas por municipio\nCorrelación de Spearman",
        "Relación entre variables",
        "Municipio",
        "heatmap_correlaciones_por_municipio.png"
    )


# ============================================================
# HEATMAP MUNICIPIO × SEMANA
# ============================================================

def heatmaps_temporales(
    df,
    temperatura,
    humedad,
    precipitacion
):

    configuraciones = [
        (
            temperatura,
            "Temperatura media por municipio y semana",
            "heatmap_temperatura_semanal.png",
            ".1f"
        ),
        (
            humedad,
            "Humedad media por municipio y semana",
            "heatmap_humedad_semanal.png",
            ".1f"
        ),
        (
            precipitacion,
            "Precipitación por municipio y semana",
            "heatmap_precipitacion_semanal.png",
            ".1f"
        )
    ]

    for (
        variable,
        titulo,
        archivo,
        formato
    ) in configuraciones:

        matriz = df.pivot_table(
            index="municipio",
            columns="semana_epidemiologica",
            values=variable,
            aggfunc="mean"
        )

        matriz.columns = [
            f"SE{int(x)}"
            for x in matriz.columns
        ]

        heatmap(
            matriz,
            titulo,
            "Semana epidemiológica",
            "Municipio",
            archivo,
            formato
        )


# ============================================================
# EVOLUCIÓN SEMANAL
# ============================================================

def evolucion_variable(
    df,
    variable,
    ylabel,
    titulo,
    archivo
):

    plt.figure(
        figsize=(11, 7)
    )

    for municipio, grupo in df.groupby(
        "municipio"
    ):

        grupo = grupo.sort_values(
            "semana_epidemiologica"
        )

        plt.plot(
            grupo[
                "semana_epidemiologica"
            ],
            grupo[variable],
            marker="o",
            label=municipio
        )

    plt.title(
        titulo
    )

    plt.xlabel(
        "Semana epidemiológica"
    )

    plt.ylabel(
        ylabel
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    guardar_figura(
        archivo
    )


def evoluciones(
    df,
    temperatura,
    humedad,
    precipitacion
):

    evolucion_variable(
        df,
        temperatura,
        "Temperatura media (°C)",
        "Evolución semanal de temperatura por municipio",
        "evolucion_temperatura.png"
    )

    evolucion_variable(
        df,
        humedad,
        "Humedad relativa media (%)",
        "Evolución semanal de humedad por municipio",
        "evolucion_humedad.png"
    )

    evolucion_variable(
        df,
        precipitacion,
        "Precipitación",
        "Evolución semanal de precipitación por municipio",
        "evolucion_precipitacion.png"
    )


# ============================================================
# SCATTER INTERPRETATIVO
# TEMPERATURA + HUMEDAD + PRECIPITACIÓN
# ============================================================

def scatter_multivariable(
    df,
    temperatura,
    humedad,
    precipitacion
):

    plt.figure(
        figsize=(11, 8)
    )

    precip = df[
        precipitacion
    ].fillna(0)

    # El tamaño representa precipitación.
    # Se normaliza únicamente para visualización.
    max_precip = precip.max()

    if max_precip > 0:

        tamanos = (
            60
            +
            (precip / max_precip)
            * 500
        )

    else:

        tamanos = np.repeat(
            80,
            len(df)
        )

    municipios = sorted(
        df["municipio"].unique()
    )

    for municipio in municipios:

        mascara = (
            df["municipio"]
            == municipio
        )

        plt.scatter(
            df.loc[
                mascara,
                temperatura
            ],
            df.loc[
                mascara,
                humedad
            ],
            s=tamanos[mascara],
            alpha=0.65,
            label=municipio
        )

    plt.title(
        "Relación temperatura-humedad-precipitación\n"
        "Tamaño del punto = precipitación semanal"
    )

    plt.xlabel(
        "Temperatura media (°C)"
    )

    plt.ylabel(
        "Humedad relativa media (%)"
    )

    plt.legend()

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        "temperatura_humedad_precipitacion.png"
    )


# ============================================================
# SCATTERS BIVARIADOS
# ============================================================

def scatter_por_municipio(
    df,
    x,
    y,
    xlabel,
    ylabel,
    titulo,
    archivo
):

    plt.figure(
        figsize=(10, 7)
    )

    for municipio, grupo in df.groupby(
        "municipio"
    ):

        plt.scatter(
            grupo[x],
            grupo[y],
            s=70,
            alpha=0.7,
            label=municipio
        )

    plt.title(
        titulo
    )

    plt.xlabel(
        xlabel
    )

    plt.ylabel(
        ylabel
    )

    plt.legend()

    plt.grid(
        alpha=0.2
    )

    guardar_figura(
        archivo
    )


def graficos_relaciones(
    df,
    temperatura,
    humedad,
    precipitacion
):

    scatter_por_municipio(
        df,
        temperatura,
        humedad,
        "Temperatura media (°C)",
        "Humedad relativa media (%)",
        "Temperatura vs humedad por municipio-semana",
        "temperatura_vs_humedad.png"
    )

    scatter_por_municipio(
        df,
        temperatura,
        precipitacion,
        "Temperatura media (°C)",
        "Precipitación",
        "Temperatura vs precipitación por municipio-semana",
        "temperatura_vs_precipitacion.png"
    )

    scatter_por_municipio(
        df,
        humedad,
        precipitacion,
        "Humedad relativa media (%)",
        "Precipitación",
        "Humedad vs precipitación por municipio-semana",
        "humedad_vs_precipitacion.png"
    )


# ============================================================
# COMBINACIÓN TEMPORAL
# TEMPERATURA + HUMEDAD
# ============================================================

def temperatura_humedad_semanal(
    df,
    temperatura,
    humedad
):

    resumen = (
        df.groupby(
            "semana_epidemiologica"
        )
        .agg(
            temperatura=(
                temperatura,
                "mean"
            ),
            humedad=(
                humedad,
                "mean"
            )
        )
        .reset_index()
    )

    fig, ax1 = plt.subplots(
        figsize=(11, 7)
    )

    ax1.plot(
        resumen[
            "semana_epidemiologica"
        ],
        resumen[
            "temperatura"
        ],
        marker="o"
    )

    ax1.set_xlabel(
        "Semana epidemiológica"
    )

    ax1.set_ylabel(
        "Temperatura media (°C)"
    )

    ax2 = ax1.twinx()

    ax2.plot(
        resumen[
            "semana_epidemiologica"
        ],
        resumen[
            "humedad"
        ],
        marker="s",
        linestyle="--"
    )

    ax2.set_ylabel(
        "Humedad relativa media (%)"
    )

    plt.title(
        "Evolución conjunta de temperatura y humedad"
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUTPUT_DIR,
            "temperatura_humedad_semanal.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# PRECIPITACIÓN + HUMEDAD
# ============================================================

def precipitacion_humedad_semanal(
    df,
    precipitacion,
    humedad
):

    resumen = (
        df.groupby(
            "semana_epidemiologica"
        )
        .agg(
            precipitacion=(
                precipitacion,
                "mean"
            ),
            humedad=(
                humedad,
                "mean"
            )
        )
        .reset_index()
    )

    fig, ax1 = plt.subplots(
        figsize=(11, 7)
    )

    ax1.bar(
        resumen[
            "semana_epidemiologica"
        ],
        resumen[
            "precipitacion"
        ],
        alpha=0.6
    )

    ax1.set_xlabel(
        "Semana epidemiológica"
    )

    ax1.set_ylabel(
        "Precipitación media"
    )

    ax2 = ax1.twinx()

    ax2.plot(
        resumen[
            "semana_epidemiologica"
        ],
        resumen[
            "humedad"
        ],
        marker="o"
    )

    ax2.set_ylabel(
        "Humedad relativa media (%)"
    )

    plt.title(
        "Precipitación y humedad por semana epidemiológica"
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUTPUT_DIR,
            "precipitacion_humedad_semanal.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# BOXPLOTS
# ============================================================

def boxplot_variable(
    df,
    variable,
    ylabel,
    titulo,
    archivo
):

    municipios = sorted(
        df["municipio"].unique()
    )

    datos = [
        df.loc[
            df["municipio"] == municipio,
            variable
        ].dropna().values

        for municipio in municipios
    ]

    plt.figure(
        figsize=(11, 7)
    )

    plt.boxplot(
        datos,
        tick_labels=municipios
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


def boxplots(
    df,
    temperatura,
    humedad,
    precipitacion
):

    boxplot_variable(
        df,
        temperatura,
        "Temperatura media (°C)",
        "Distribución semanal de temperatura por municipio",
        "boxplot_temperatura.png"
    )

    boxplot_variable(
        df,
        humedad,
        "Humedad relativa media (%)",
        "Distribución semanal de humedad por municipio",
        "boxplot_humedad.png"
    )

    boxplot_variable(
        df,
        precipitacion,
        "Precipitación",
        "Distribución semanal de precipitación por municipio",
        "boxplot_precipitacion.png"
    )


# ============================================================
# PERFIL CLIMÁTICO NORMALIZADO
# ============================================================

def perfil_climatico(
    df,
    temperatura,
    humedad,
    precipitacion
):

    perfil = (
        df.groupby(
            "municipio"
        )[
            [
                temperatura,
                humedad,
                precipitacion
            ]
        ]
        .mean()
    )

    normalizado = perfil.copy()

    for columna in normalizado.columns:

        minimo = normalizado[
            columna
        ].min()

        maximo = normalizado[
            columna
        ].max()

        if maximo != minimo:

            normalizado[columna] = (
                normalizado[columna]
                - minimo
            ) / (
                maximo
                - minimo
            )

        else:

            normalizado[columna] = 0

    normalizado.columns = [
        "Temperatura",
        "Humedad",
        "Precipitación"
    ]

    normalizado.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "perfil_climatico_normalizado.csv"
        ),
        encoding="utf-8-sig"
    )

    heatmap(
        normalizado,
        "Perfil climático relativo por municipio\n"
        "Variables normalizadas entre 0 y 1",
        "Variable climática",
        "Municipio",
        "heatmap_perfil_climatico.png"
    )


# ============================================================
# VARIABILIDAD POR MUNICIPIO
# ============================================================

def variabilidad_climatica(
    df,
    temperatura,
    humedad,
    precipitacion
):

    variabilidad = (
        df.groupby(
            "municipio"
        )[
            [
                temperatura,
                humedad,
                precipitacion
            ]
        ]
        .std()
    )

    variabilidad.columns = [
        "variabilidad_temperatura",
        "variabilidad_humedad",
        "variabilidad_precipitacion"
    ]

    print(
        "\n========== VARIABILIDAD CLIMÁTICA =========="
    )

    print(
        variabilidad.round(2).to_string()
    )

    variabilidad.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "variabilidad_climatica.csv"
        ),
        encoding="utf-8-sig"
    )

    # Normalizamos porque las unidades son diferentes
    visual = variabilidad.copy()

    for columna in visual.columns:

        maximo = visual[columna].max()

        if maximo > 0:

            visual[columna] = (
                visual[columna]
                / maximo
            )

    visual.columns = [
        "Temperatura",
        "Humedad",
        "Precipitación"
    ]

    heatmap(
        visual,
        "Variabilidad climática relativa por municipio",
        "Variable",
        "Municipio",
        "heatmap_variabilidad_climatica.png"
    )


# ============================================================
# SEMANAS EXTREMAS
# ============================================================

def semanas_extremas(
    df,
    temperatura,
    humedad,
    precipitacion
):

    resultados = []

    for municipio, grupo in df.groupby(
        "municipio"
    ):

        grupo = grupo.copy()

        fila_temp_max = grupo.loc[
            grupo[
                temperatura
            ].idxmax()
        ]

        fila_temp_min = grupo.loc[
            grupo[
                temperatura
            ].idxmin()
        ]

        fila_humedad = grupo.loc[
            grupo[
                humedad
            ].idxmax()
        ]

        fila_precip = grupo.loc[
            grupo[
                precipitacion
            ].idxmax()
        ]

        resultados.append({
            "municipio":
                municipio,

            "semana_temp_max":
                int(
                    fila_temp_max[
                        "semana_epidemiologica"
                    ]
                ),

            "temp_max":
                fila_temp_max[
                    temperatura
                ],

            "semana_temp_min":
                int(
                    fila_temp_min[
                        "semana_epidemiologica"
                    ]
                ),

            "temp_min":
                fila_temp_min[
                    temperatura
                ],

            "semana_humedad_max":
                int(
                    fila_humedad[
                        "semana_epidemiologica"
                    ]
                ),

            "humedad_max":
                fila_humedad[
                    humedad
                ],

            "semana_precipitacion_max":
                int(
                    fila_precip[
                        "semana_epidemiologica"
                    ]
                ),

            "precipitacion_max":
                fila_precip[
                    precipitacion
                ]
        })

    extremos = pd.DataFrame(
        resultados
    )

    print(
        "\n========== SEMANAS CLIMÁTICAS EXTREMAS =========="
    )

    print(
        extremos.round(2).to_string(
            index=False
        )
    )

    extremos.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "semanas_extremas.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# MATRIZ DE DISPERSIÓN
# ============================================================

def matriz_dispersion(
    df,
    temperatura,
    humedad,
    precipitacion
):

    variables = [
        temperatura,
        humedad,
        precipitacion
    ]

    datos = df[
        variables
    ].dropna()

    nombres = [
        "Temperatura",
        "Humedad",
        "Precipitación"
    ]

    fig, axes = plt.subplots(
        3,
        3,
        figsize=(11, 11)
    )

    for i in range(3):

        for j in range(3):

            ax = axes[i, j]

            if i == j:

                ax.hist(
                    datos[
                        variables[i]
                    ],
                    bins=10,
                    edgecolor="black"
                )

            else:

                ax.scatter(
                    datos[
                        variables[j]
                    ],
                    datos[
                        variables[i]
                    ],
                    alpha=0.65
                )

            if i == 2:

                ax.set_xlabel(
                    nombres[j]
                )

            if j == 0:

                ax.set_ylabel(
                    nombres[i]
                )

    fig.suptitle(
        "Matriz exploratoria de variables climáticas",
        fontsize=14
    )

    fig.tight_layout(
        rect=[0, 0, 1, 0.97]
    )

    fig.savefig(
        os.path.join(
            OUTPUT_DIR,
            "matriz_dispersion_climatica.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# RESUMEN
# ============================================================

def generar_resumen(
    df,
    temperatura,
    humedad,
    precipitacion
):

    correlacion = df[
        [
            temperatura,
            humedad,
            precipitacion
        ]
    ].corr(
        method="spearman"
    )

    temp_hum = correlacion.loc[
        temperatura,
        humedad
    ]

    temp_prec = correlacion.loc[
        temperatura,
        precipitacion
    ]

    hum_prec = correlacion.loc[
        humedad,
        precipitacion
    ]

    contenido = f"""
EDA CLIMÁTICO AVANZADO
======================

FUENTE
------
SENAMHI Bolivia - WIS 2.0

UNIDAD PRINCIPAL DE ANÁLISIS
----------------------------
Municipio - semana epidemiológica

Observaciones analizadas:
{len(df)}

Municipios:
{df["municipio"].nunique()}

Semanas epidemiológicas:
{df["semana_epidemiologica"].nunique()}

CORRELACIONES DE SPEARMAN
-------------------------
Temperatura - Humedad:
{temp_hum:.3f}

Temperatura - Precipitación:
{temp_prec:.3f}

Humedad - Precipitación:
{hum_prec:.3f}

INTERPRETACIÓN
--------------
Las correlaciones representan asociaciones exploratorias
entre las variables climáticas observadas.

Un coeficiente positivo indica que ambas variables tienden
a aumentar conjuntamente, mientras que un coeficiente
negativo indica que una tiende a disminuir cuando la otra
aumenta.

Estas asociaciones no deben interpretarse como relaciones
causales.

Los análisis por municipio permiten comprobar si las
relaciones generales se mantienen o cambian entre zonas.

Los heatmaps temporales permiten identificar semanas con
condiciones climáticas particularmente diferentes.

El perfil normalizado permite comparar municipios aunque
temperatura, humedad y precipitación utilicen escalas
distintas.

LIMITACIONES
------------
1. La cobertura climática no es igual para todos los
   municipios.

2. Algunas semanas tienen menos días observados.

3. Palos Blancos y San Buenaventura presentan menor
   cobertura que Guayaramerín e Ixiamas.

4. Los resultados corresponden al período disponible
   durante 2026.

5. Correlación no implica causalidad.

6. Las relaciones climáticas observadas no implican por
   sí mismas una relación con dengue o malaria. Esa parte
   corresponde al EDA integrado.

CONCLUSIÓN METODOLÓGICA
-----------------------
El EDA climático permite estudiar no solamente los niveles
promedio de temperatura, humedad y precipitación, sino
también su evolución temporal, variabilidad, relaciones y
diferencias entre municipios.

Estos resultados sirven como base para la posterior
integración con información epidemiológica.
"""

    archivo = os.path.join(
        OUTPUT_DIR,
        "resumen_eda_climatico.txt"
    )

    with open(
        archivo,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            contenido.strip()
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "EDA CLIMÁTICO AVANZADO - SENAMHI"
    )

    print(
        "=========================================="
    )

    semanal, diario = cargar_datos()

    (
        temperatura,
        humedad,
        precipitacion
    ) = detectar_columnas(
        semanal
    )

    informacion_general(
        semanal
    )

    calidad_datos(
        semanal
    )

    estadisticas_descriptivas(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    correlaciones(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    correlaciones_por_municipio(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    heatmaps_temporales(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    evoluciones(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    scatter_multivariable(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    graficos_relaciones(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    temperatura_humedad_semanal(
        semanal,
        temperatura,
        humedad
    )

    precipitacion_humedad_semanal(
        semanal,
        precipitacion,
        humedad
    )

    boxplots(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    perfil_climatico(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    variabilidad_climatica(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    semanas_extremas(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    matriz_dispersion(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    generar_resumen(
        semanal,
        temperatura,
        humedad,
        precipitacion
    )

    print(
        "\n=========================================="
    )

    print(
        "✓ EDA CLIMÁTICO AVANZADO COMPLETADO"
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