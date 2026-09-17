"""
Procesamiento de datos climáticos SENAMHI
Proyecto: Predicción temprana de brotes de Dengue y Malaria

Flujo:
RAW SENAMHI
    ↓
Control de calidad
    ↓
Agregación diaria
    ↓
Agregación por semana epidemiológica

IMPORTANTE:
- No modifica los datos RAW.
- No genera datos sintéticos.
- No imputa observaciones faltantes.
- Los valores sospechosos se conservan en el control de calidad,
  pero no se utilizan para la agregación analítica.
"""

import os
import pandas as pd


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RAW_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "clima",
    "senamhi",
    "senamhi_raw_SE01_13_2026.csv"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

DIARIO_FILE = os.path.join(
    PROCESSED_DIR,
    "clima_diario.csv"
)

SEMANAL_FILE = os.path.join(
    PROCESSED_DIR,
    "clima_semanal.csv"
)

QC_FILE = os.path.join(
    PROCESSED_DIR,
    "control_calidad_clima.csv"
)


# ============================================================
# VARIABLES SENAMHI
# ============================================================

TEMP = "air_temperature"

HUMEDAD = "relative_humidity"

PRECIP = (
    "total_precipitation_or_total_water_equivalent"
)


# ============================================================
# CARGA
# ============================================================

def cargar_datos():

    print("\nCargando datos RAW de SENAMHI...")

    df = pd.read_csv(RAW_FILE)

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"],
        utc=True
    )

    df["valor"] = pd.to_numeric(
        df["valor"],
        errors="coerce"
    )

    print("✓ Registros cargados:", len(df))

    return df


# ============================================================
# CONTROL DE CALIDAD
# ============================================================

def aplicar_control_calidad(df):

    """
    Marca valores físicamente sospechosos.

    IMPORTANTE:
    Las reglas no modifican el valor original.
    Solo generan una bandera qc_sospechoso.
    """

    datos = df.copy()

    datos["qc_sospechoso"] = False

    datos["motivo_qc"] = ""


    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------
    # Límites amplios de plausibilidad para detectar errores
    # evidentes de codificación/sensor, no para eliminar
    # extremos meteorológicos normales.

    mascara = (
        (datos["variable"] == TEMP) &
        (
            (datos["valor"] < -10) |
            (datos["valor"] > 50)
        )
    )

    datos.loc[
        mascara,
        "qc_sospechoso"
    ] = True

    datos.loc[
        mascara,
        "motivo_qc"
    ] = "temperatura_fuera_rango_plausible"


    # --------------------------------------------------------
    # HUMEDAD
    # --------------------------------------------------------

    mascara = (
        (datos["variable"] == HUMEDAD) &
        (
            (datos["valor"] < 0) |
            (datos["valor"] > 100)
        )
    )

    datos.loc[
        mascara,
        "qc_sospechoso"
    ] = True

    datos.loc[
        mascara,
        "motivo_qc"
    ] = "humedad_fuera_rango_0_100"


    # --------------------------------------------------------
    # PRECIPITACIÓN
    # --------------------------------------------------------

    # Valores negativos son físicamente inválidos.

    mascara_negativa = (
        (datos["variable"] == PRECIP) &
        (datos["valor"] < 0)
    )

    datos.loc[
        mascara_negativa,
        "qc_sospechoso"
    ] = True

    datos.loc[
        mascara_negativa,
        "motivo_qc"
    ] = "precipitacion_negativa"


    # --------------------------------------------------------
    # EVENTO ANÓMALO IDENTIFICADO EN EL EDA
    # --------------------------------------------------------
    #
    # En San Buenaventura encontramos una secuencia de
    # 1389.4 kg/m² en ventanas móviles de 24 h.
    #
    # NO alteramos esos valores.
    # Los marcamos como sospechosos para excluirlos de
    # la agregación analítica.
    #
    # La regla > 1000 se usa aquí como bandera conservadora
    # para el evento extremo observado en este dataset.
    # No debe interpretarse como un umbral meteorológico
    # universal.

    mascara_extrema = (
        (datos["variable"] == PRECIP) &
        (datos["valor"] > 1000)
    )

    datos.loc[
        mascara_extrema,
        "qc_sospechoso"
    ] = True

    datos.loc[
        mascara_extrema,
        "motivo_qc"
    ] = "precipitacion_extrema_requiere_validacion"


    # --------------------------------------------------------
    # GUARDAR CONTROL DE CALIDAD
    # --------------------------------------------------------

    datos.to_csv(
        QC_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    sospechosos = datos[
        datos["qc_sospechoso"]
    ]

    print("\n========== CONTROL DE CALIDAD ==========")

    print(
        "Registros sospechosos:",
        len(sospechosos)
    )

    if not sospechosos.empty:

        print("\nPor motivo:")

        print(
            sospechosos[
                "motivo_qc"
            ].value_counts()
        )

    print(
        "\n✓ Control de calidad guardado."
    )

    return datos


# ============================================================
# PREPARAR DATOS VÁLIDOS
# ============================================================

def obtener_datos_validos(df):

    validos = df[
        ~df["qc_sospechoso"]
    ].copy()

    validos = validos.dropna(
        subset=["valor"]
    )

    return validos


# ============================================================
# TEMPERATURA DIARIA
# ============================================================

def temperatura_diaria(df):

    datos = df[
        df["variable"] == TEMP
    ].copy()

    datos["fecha"] = (
        datos["fecha_hora"]
        .dt.floor("D")
    )

    diario = (
        datos.groupby(
            ["municipio", "fecha"]
        )["valor"]
        .agg(
            temperatura_media="mean",
            temperatura_min="min",
            temperatura_max="max",
            observaciones_temperatura="count"
        )
        .reset_index()
    )

    return diario


# ============================================================
# HUMEDAD DIARIA
# ============================================================

def humedad_diaria(df):

    datos = df[
        df["variable"] == HUMEDAD
    ].copy()

    datos["fecha"] = (
        datos["fecha_hora"]
        .dt.floor("D")
    )

    diario = (
        datos.groupby(
            ["municipio", "fecha"]
        )["valor"]
        .agg(
            humedad_media="mean",
            humedad_min="min",
            humedad_max="max",
            observaciones_humedad="count"
        )
        .reset_index()
    )

    return diario


# ============================================================
# PRECIPITACIÓN DIARIA
# ============================================================

def precipitacion_diaria(df):

    """
    SENAMHI entrega ventanas móviles de precipitación
    acumulada en 24 horas.

    No podemos sumar todas las observaciones horarias.

    Para obtener una observación diaria comparable:
    seleccionamos UNA observación de 24 h por
    municipio y fecha.

    Usamos como referencia las 12:00 UTC y seleccionamos
    la observación disponible más cercana a esa hora.
    """

    datos = df[
        df["variable"] == PRECIP
    ].copy()

    datos["fecha"] = (
        datos["fecha_hora"]
        .dt.floor("D")
    )

    datos["hora"] = (
        datos["fecha_hora"].dt.hour
    )

    HORA_REFERENCIA = 12

    datos["distancia_hora"] = (
        datos["hora"] - HORA_REFERENCIA
    ).abs()

    # Ordenamos para que el primer registro de cada
    # municipio/día sea el más cercano a 12 UTC.

    datos = datos.sort_values(
        [
            "municipio",
            "fecha",
            "distancia_hora",
            "fecha_hora"
        ]
    )

    diario = (
        datos
        .drop_duplicates(
            subset=[
                "municipio",
                "fecha"
            ],
            keep="first"
        )
        [
            [
                "municipio",
                "fecha",
                "valor",
                "fecha_hora"
            ]
        ]
        .copy()
    )

    diario = diario.rename(
        columns={
            "valor": "precipitacion_24h",
            "fecha_hora": "hora_reporte_precipitacion"
        }
    )

    return diario


# ============================================================
# UNIR DATOS DIARIOS
# ============================================================

def construir_diario(df):

    temp = temperatura_diaria(df)

    humedad = humedad_diaria(df)

    precip = precipitacion_diaria(df)


    diario = temp.merge(
        humedad,
        on=[
            "municipio",
            "fecha"
        ],
        how="outer"
    )


    diario = diario.merge(
        precip,
        on=[
            "municipio",
            "fecha"
        ],
        how="outer"
    )


    diario = diario.sort_values(
        [
            "municipio",
            "fecha"
        ]
    )


    diario.to_csv(
        DIARIO_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    print("\n========== DATASET DIARIO ==========")

    print(
        "Filas:",
        len(diario)
    )

    print(
        "Municipios:",
        diario["municipio"].nunique()
    )

    print(
        "Desde:",
        diario["fecha"].min()
    )

    print(
        "Hasta:",
        diario["fecha"].max()
    )

    print(
        "\nRegistros por municipio:"
    )

    print(
        diario[
            "municipio"
        ].value_counts()
    )


    return diario


# ============================================================
# SEMANA EPIDEMIOLÓGICA
# ============================================================

def agregar_semana_epidemiologica(df):

    datos = df.copy()

    # ISO week se utilizará como aproximación operacional
    # de semana epidemiológica para este procesamiento.
    # Para 2026, guardamos también el año ISO para evitar
    # ambigüedad entre años.

    iso = datos["fecha"].dt.isocalendar()

    datos["anio"] = iso.year.astype(int)

    datos["semana_epidemiologica"] = (
        iso.week.astype(int)
    )


    semanal = (
        datos.groupby(
            [
                "municipio",
                "anio",
                "semana_epidemiologica"
            ]
        )
        .agg(

            temperatura_media=(
                "temperatura_media",
                "mean"
            ),

            temperatura_min=(
                "temperatura_min",
                "min"
            ),

            temperatura_max=(
                "temperatura_max",
                "max"
            ),

            humedad_media=(
                "humedad_media",
                "mean"
            ),

            humedad_min=(
                "humedad_min",
                "min"
            ),

            humedad_max=(
                "humedad_max",
                "max"
            ),

            precipitacion_total_mm=(
                "precipitacion_24h",
                "sum"
            ),

            dias_con_temperatura=(
                "temperatura_media",
                "count"
            ),

            dias_con_humedad=(
                "humedad_media",
                "count"
            ),

            dias_con_precipitacion=(
                "precipitacion_24h",
                "count"
            )
        )
        .reset_index()
    )

    # ========================================================
    # LIMITAR AL PERIODO EPIDEMIOLÓGICO DEL PROYECTO
    # ========================================================

    # Los datos epidemiológicos disponibles corresponden
    # únicamente a las semanas epidemiológicas 1 a 13.
    # Por eso se excluye la semana 14 del dataset procesado.

    semanal = semanal[
        semanal["semana_epidemiologica"].between(1, 13)
    ].copy()


    # ========================================================
    # CALIDAD DE COBERTURA SEMANAL
    # ========================================================

    # Se considera cobertura suficiente cuando existen
    # observaciones en al menos 5 de los 7 días de la semana
    # para las tres variables climáticas.

    semanal["cobertura_suficiente"] = (
        (semanal["dias_con_temperatura"] >= 5) &
        (semanal["dias_con_humedad"] >= 5) &
        (semanal["dias_con_precipitacion"] >= 5)
    )


    semanal = semanal.sort_values(
        [
            "municipio",
            "semana_epidemiologica"
        ]
    )


    semanal.to_csv(
        SEMANAL_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    print("\n========== DATASET SEMANAL ==========")

    print(
        "Filas:",
        len(semanal)
    )

    print(
        "\nSemanas disponibles:"
    )

    print(
        sorted(
            semanal[
                "semana_epidemiologica"
            ].unique()
        )
    )


    print(
        "\nFilas por municipio:"
    )

    print(
        semanal[
            "municipio"
        ].value_counts()
    )


    print(
        "\nCobertura semanal:"
    )

    print(
        semanal[
            [
                "municipio",
                "semana_epidemiologica",
                "dias_con_temperatura",
                "dias_con_humedad",
                "dias_con_precipitacion",
                "cobertura_suficiente"
            ]
        ].to_string(
            index=False
        )
    )


    return semanal


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "PROCESAMIENTO CLIMÁTICO SENAMHI"
    )

    print(
        "=========================================="
    )


    # 1. RAW

    df = cargar_datos()


    # 2. CONTROL DE CALIDAD

    df_qc = aplicar_control_calidad(
        df
    )


    # 3. DATOS VÁLIDOS

    validos = obtener_datos_validos(
        df_qc
    )


    print(
        "\nRegistros utilizados:",
        len(validos),
        "/",
        len(df_qc)
    )


    # 4. DIARIO

    diario = construir_diario(
        validos
    )


    # 5. SEMANAL

    semanal = agregar_semana_epidemiologica(
        diario
    )


    print(
        "\n=========================================="
    )

    print(
        "✓ PROCESAMIENTO COMPLETADO"
    )

    print(
        "=========================================="
    )


    print(
        "\nArchivos generados:"
    )

    print(
        "\n1.",
        QC_FILE
    )

    print(
        "\n2.",
        DIARIO_FILE
    )

    print(
        "\n3.",
        SEMANAL_FILE
    )


if __name__ == "__main__":
    main()