"""
Integración de datos climáticos y epidemiológicos
Proyecto: Predicción temprana de brotes de Dengue y Malaria

Fuentes:
- SENAMHI Bolivia: clima disponible SE3-SE13 de 2026
- Ministerio de Salud y Deportes:
  dengue y malaria acumulados SE1-SE13 de 2026

IMPORTANTE:
- No se reconstruyen casos epidemiológicos semanales municipales.
- No se interpreta la ausencia de malaria como cero casos.
- No se generan datos sintéticos.
- Se documenta el desfase temporal entre las fuentes.
- Se conserva información sobre la cobertura climática.
"""

import os
import pandas as pd


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CLIMA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "clima_semanal.csv"
)

DENGUE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "epidemiologia",
    "dengue_bolivia_municipal_SE01_13_2026.csv"
)

MALARIA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "epidemiologia",
    "malaria_bolivia_municipal_SE01_13_2026.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "dataset_integrado_municipal.csv"
)


# ============================================================
# CONFIGURACIÓN DEL PERÍODO
# ============================================================

ANIO = 2026

SEMANA_INICIO_CLIMA = 3
SEMANA_FIN_CLIMA = 13

# SE3-SE13 = 11 semanas
SEMANAS_ESPERADAS = 11

# 11 semanas x 7 días
DIAS_ESPERADOS = 77


# ============================================================
# CARGAR DATOS
# ============================================================

def cargar_datos():

    print("\nCargando datasets...")

    clima = pd.read_csv(CLIMA_FILE)
    dengue = pd.read_csv(DENGUE_FILE)
    malaria = pd.read_csv(MALARIA_FILE)

    print("Clima semanal:", len(clima))
    print("Dengue municipal:", len(dengue))
    print("Malaria municipal:", len(malaria))

    return clima, dengue, malaria


# ============================================================
# NORMALIZAR MUNICIPIOS
# ============================================================

def normalizar_municipios(df):

    """
    Normalización básica para evitar errores de unión
    causados por espacios o diferencias de mayúsculas.

    No modifica nombres mediante aproximaciones ni
    correspondencias artificiales.
    """

    datos = df.copy()

    datos["municipio"] = (
        datos["municipio"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return datos


# ============================================================
# RESUMIR CLIMA POR MUNICIPIO
# ============================================================

def resumir_clima(clima):

    print("\n========== RESUMEN CLIMÁTICO ==========")

    clima = clima.copy()

    # --------------------------------------------------------
    # LIMITAR AL PERÍODO CLIMÁTICO DISPONIBLE
    # --------------------------------------------------------

    clima = clima[
        clima["semana_epidemiologica"].between(
            SEMANA_INICIO_CLIMA,
            SEMANA_FIN_CLIMA
        )
    ].copy()

    # --------------------------------------------------------
    # NORMALIZAR COBERTURA SUFICIENTE
    # --------------------------------------------------------

    if clima["cobertura_suficiente"].dtype != bool:

        clima["cobertura_suficiente"] = (
            clima["cobertura_suficiente"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("true")
        )

    # Cada fila representa una semana disponible.

    clima["semana_disponible"] = 1


    # --------------------------------------------------------
    # AGREGACIÓN POR MUNICIPIO
    # --------------------------------------------------------

    resumen = (
        clima.groupby("municipio")
        .agg(

            temperatura_media_periodo=(
                "temperatura_media",
                "mean"
            ),

            temperatura_min_periodo=(
                "temperatura_min",
                "min"
            ),

            temperatura_max_periodo=(
                "temperatura_max",
                "max"
            ),

            humedad_media_periodo=(
                "humedad_media",
                "mean"
            ),

            humedad_min_periodo=(
                "humedad_min",
                "min"
            ),

            humedad_max_periodo=(
                "humedad_max",
                "max"
            ),

            precipitacion_total_periodo_mm=(
                "precipitacion_total_mm",
                "sum"
            ),

            semanas_climaticas_disponibles=(
                "semana_disponible",
                "sum"
            ),

            semanas_cobertura_suficiente=(
                "cobertura_suficiente",
                "sum"
            ),

            dias_temperatura=(
                "dias_con_temperatura",
                "sum"
            ),

            dias_humedad=(
                "dias_con_humedad",
                "sum"
            ),

            dias_precipitacion=(
                "dias_con_precipitacion",
                "sum"
            )
        )
        .reset_index()
    )


    # ========================================================
    # COBERTURA SEMANAL
    # ========================================================

    resumen[
        "porcentaje_semanas_cobertura_suficiente"
    ] = (
        resumen["semanas_cobertura_suficiente"]
        / SEMANAS_ESPERADAS
        * 100
    ).round(2)


    # ========================================================
    # COBERTURA POR DÍAS
    # ========================================================

    resumen["porcentaje_dias_temperatura"] = (
        resumen["dias_temperatura"]
        / DIAS_ESPERADOS
        * 100
    ).round(2)

    resumen["porcentaje_dias_humedad"] = (
        resumen["dias_humedad"]
        / DIAS_ESPERADOS
        * 100
    ).round(2)

    resumen["porcentaje_dias_precipitacion"] = (
        resumen["dias_precipitacion"]
        / DIAS_ESPERADOS
        * 100
    ).round(2)


    # ========================================================
    # PRECIPITACIÓN NORMALIZADA
    # ========================================================

    # El total de precipitación puede resultar engañoso
    # cuando existen diferentes cantidades de días observados.
    #
    # Por eso conservamos:
    #
    # 1. precipitación total observada
    # 2. precipitación media por día observado

    resumen[
        "precipitacion_media_dia_observado"
    ] = (
        resumen["precipitacion_total_periodo_mm"]
        / resumen["dias_precipitacion"]
    ).round(2)


    # ========================================================
    # COBERTURA CLIMÁTICA GENERAL
    # ========================================================

    # Consideramos cobertura alta cuando las tres variables
    # tienen datos para al menos el 80 % de los días esperados.
    #
    # Esto NO elimina registros.
    # Solo crea una bandera de calidad.

    resumen["cobertura_climatica_alta"] = (
        (resumen["porcentaje_dias_temperatura"] >= 80) &
        (resumen["porcentaje_dias_humedad"] >= 80) &
        (resumen["porcentaje_dias_precipitacion"] >= 80)
    )


    # ========================================================
    # PERÍODO CLIMÁTICO
    # ========================================================

    resumen["periodo_clima"] = "SE3-13 2026"


    print(
        resumen.to_string(
            index=False
        )
    )

    return resumen


# ============================================================
# PREPARAR DENGUE
# ============================================================

def preparar_dengue(dengue):

    columnas = [
        "departamento",
        "municipio",
        "anio",
        "casos_dengue_acumulados_se1_13",
        "incidencia_por_10000_hab"
    ]

    dengue = dengue[columnas].copy()

    dengue = dengue.rename(
        columns={
            "departamento":
                "departamento_dengue"
        }
    )

    return dengue


# ============================================================
# PREPARAR MALARIA
# ============================================================

def preparar_malaria(malaria):

    columnas = [
        "sedes_segun_tabla",
        "municipio",
        "anio",
        "p_vivax",
        "p_falciparum",
        "mixta",
        "total_malaria"
    ]

    malaria = malaria[columnas].copy()

    malaria = malaria.rename(
        columns={
            "sedes_segun_tabla":
                "departamento_malaria"
        }
    )

    return malaria


# ============================================================
# INTEGRACIÓN
# ============================================================

def integrar(clima, dengue, malaria):

    print("\n========== INTEGRACIÓN ==========")

    # --------------------------------------------------------
    # CLIMA + DENGUE
    # --------------------------------------------------------

    integrado = clima.merge(
        dengue,
        on="municipio",
        how="left",
        validate="one_to_one"
    )


    # --------------------------------------------------------
    # CLIMA + DENGUE + MALARIA
    # --------------------------------------------------------

    integrado = integrado.merge(
        malaria,
        on=[
            "municipio",
            "anio"
        ],
        how="left",
        validate="one_to_one"
    )


    # ========================================================
    # DISPONIBILIDAD DE DATOS EPIDEMIOLÓGICOS
    # ========================================================

    integrado["dengue_disponible"] = (
        integrado[
            "casos_dengue_acumulados_se1_13"
        ].notna()
    )

    integrado["malaria_disponible"] = (
        integrado[
            "total_malaria"
        ].notna()
    )


    # ========================================================
    # METADATOS TEMPORALES
    # ========================================================

    integrado[
        "periodo_epidemiologia"
    ] = "SE1-13 2026"

    integrado[
        "alineacion_temporal_completa"
    ] = False


    # ========================================================
    # NOTA METODOLÓGICA
    # ========================================================

    integrado["nota_integracion"] = (
        "Clima disponible para SE3-13 de 2026; "
        "dengue y malaria corresponden a acumulados "
        "municipales SE1-13 de 2026. "
        "No se reconstruyeron casos semanales municipales "
        "ni se imputaron valores epidemiológicos ausentes."
    )


    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    integrado = integrado.sort_values(
        "municipio"
    ).reset_index(drop=True)

    return integrado


# ============================================================
# VALIDACIÓN
# ============================================================

def validar(integrado):

    print("\n========== VALIDACIÓN ==========")

    print(
        "Municipios integrados:",
        len(integrado)
    )

    print("\nMunicipios:")

    print(
        integrado[
            "municipio"
        ].tolist()
    )


    # --------------------------------------------------------
    # DENGUE
    # --------------------------------------------------------

    dengue_disponible = (
        integrado[
            "casos_dengue_acumulados_se1_13"
        ]
        .notna()
        .sum()
    )

    print(
        "\nCon información de dengue:",
        dengue_disponible,
        "/",
        len(integrado)
    )


    # --------------------------------------------------------
    # MALARIA
    # --------------------------------------------------------

    malaria_disponible = (
        integrado[
            "total_malaria"
        ]
        .notna()
        .sum()
    )

    print(
        "Con información de malaria:",
        malaria_disponible,
        "/",
        len(integrado)
    )


    # --------------------------------------------------------
    # CASOS DENGUE
    # --------------------------------------------------------

    print("\nCasos de dengue:")

    print(
        integrado[
            [
                "municipio",
                "casos_dengue_acumulados_se1_13"
            ]
        ].to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # CASOS MALARIA
    # --------------------------------------------------------

    print("\nCasos de malaria:")

    print(
        integrado[
            [
                "municipio",
                "total_malaria"
            ]
        ].to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # COBERTURA CLIMÁTICA
    # --------------------------------------------------------

    print("\nCobertura climática:")

    print(
        integrado[
            [
                "municipio",
                "semanas_climaticas_disponibles",
                "semanas_cobertura_suficiente",
                "porcentaje_semanas_cobertura_suficiente",
                "dias_precipitacion",
                "porcentaje_dias_precipitacion",
                "precipitacion_total_periodo_mm",
                "precipitacion_media_dia_observado",
                "cobertura_climatica_alta"
            ]
        ].to_string(
            index=False
        )
    )


    # ========================================================
    # RESUMEN DE CALIDAD
    # ========================================================

    print(
        "\nMunicipios con cobertura climática alta:",
        integrado[
            "cobertura_climatica_alta"
        ].sum(),
        "/",
        len(integrado)
    )


    print(
        "\nMunicipios con cobertura climática insuficiente:"
    )

    insuficientes = integrado[
        ~integrado[
            "cobertura_climatica_alta"
        ]
    ]

    if insuficientes.empty:

        print("Ninguno")

    else:

        print(
            insuficientes[
                [
                    "municipio",
                    "porcentaje_dias_temperatura",
                    "porcentaje_dias_humedad",
                    "porcentaje_dias_precipitacion"
                ]
            ].to_string(
                index=False
            )
        )


    # ========================================================
    # VALIDACIÓN TEMPORAL
    # ========================================================

    print(
        "\nAlineación temporal:"
    )

    print(
        "Clima: SE3-13 2026"
    )

    print(
        "Epidemiología: SE1-13 2026"
    )

    print(
        "Alineación completa: NO"
    )


# ============================================================
# GUARDAR
# ============================================================

def guardar(integrado):

    integrado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\n✓ Dataset integrado guardado:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=========================================="
    )

    print(
        "INTEGRACIÓN CLIMA + DENGUE + MALARIA"
    )

    print(
        "=========================================="
    )


    # --------------------------------------------------------
    # 1. CARGA
    # --------------------------------------------------------

    clima, dengue, malaria = cargar_datos()


    # --------------------------------------------------------
    # 2. NORMALIZACIÓN
    # --------------------------------------------------------

    clima = normalizar_municipios(
        clima
    )

    dengue = normalizar_municipios(
        dengue
    )

    malaria = normalizar_municipios(
        malaria
    )


    # --------------------------------------------------------
    # 3. RESUMEN CLIMÁTICO
    # --------------------------------------------------------

    clima_resumen = resumir_clima(
        clima
    )


    # --------------------------------------------------------
    # 4. PREPARAR EPIDEMIOLOGÍA
    # --------------------------------------------------------

    dengue = preparar_dengue(
        dengue
    )

    malaria = preparar_malaria(
        malaria
    )


    # --------------------------------------------------------
    # 5. INTEGRACIÓN
    # --------------------------------------------------------

    integrado = integrar(
        clima_resumen,
        dengue,
        malaria
    )


    # --------------------------------------------------------
    # 6. VALIDACIÓN
    # --------------------------------------------------------

    validar(
        integrado
    )


    # --------------------------------------------------------
    # 7. GUARDAR
    # --------------------------------------------------------

    guardar(
        integrado
    )


    print(
        "\n=========================================="
    )

    print(
        "✓ INTEGRACIÓN COMPLETADA"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()