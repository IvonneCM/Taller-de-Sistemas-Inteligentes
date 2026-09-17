"""
Pipeline reproducible de limpieza, validación e imputación de datos
Proyecto: Predicción temprana de brotes de Dengue y Malaria

Responsable: Tania Perez
Tarea: Construir pipeline reproducible de datos (Línea Base - Paso 2)
Implementa: docs/reglas_calidad_datos.md (autor: Dilan Mamani)

Este script NO vuelve a descargar ni a agregar los datos climáticos: eso ya
lo hacen scripts/descargar_senamhi.py y scripts/procesar_clima.py (Adriana).
Este pipeline toma esos resultados y los del EDA (data/processed/,
data/raw/epidemiologia/) y les aplica el contrato de calidad que todavía no
tenia una implementacion ejecutable:

1. Validacion epidemiologica (reglas COM-xx y EPI-xx de reglas_calidad_datos.md).
2. Reconstruccion de un calendario diario GLOBAL por municipio (corrige el
   riesgo documentado de desfase por reindexado ad-hoc entre grupos).
3. Imputacion climatica en el orden definido por Dilan:
   a) interpolacion temporal lineal (huecos de hasta 2 dias)
   b) mediana historica del mismo municipio y semana del anio
   c) mediana de municipios vecinos (por distancia de estacion)
   d) si nada aplica, se conserva como faltante (no se inventa el dato)
4. Reagregacion semanal desde los datos ya imputados, con nivel de
   confianza segun el porcentaje de datos faltantes (umbrales NFR-007).
5. Resumen de calidad por lote (recibidos/validos/imputados/rechazados),
   tal como pide la seccion 7 de reglas_calidad_datos.md.

IMPORTANTE:
- No se imputan casos epidemiologicos. Un reporte ausente se marca como tal,
  nunca como cero.
- No se inventan vecinos ni historial que no existen: cuando una regla no es
  aplicable con los datos actuales, se documenta explicitamente en el
  resumen en vez de forzar un resultado.
"""

import os
import json
import math
import pandas as pd
import numpy as np


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_SENAMHI = os.path.join(
    BASE_DIR, "data", "raw", "clima", "senamhi", "senamhi_raw_SE01_13_2026.csv"
)

CLIMA_DIARIO_ADRIANA = os.path.join(
    BASE_DIR, "data", "processed", "clima_diario.csv"
)

DENGUE_MUNICIPAL = os.path.join(
    BASE_DIR, "data", "raw", "epidemiologia",
    "dengue_bolivia_municipal_SE01_13_2026.csv"
)

MALARIA_MUNICIPAL = os.path.join(
    BASE_DIR, "data", "raw", "epidemiologia",
    "malaria_bolivia_municipal_SE01_13_2026.csv"
)

DENGUE_SEMANAL_NACIONAL = os.path.join(
    BASE_DIR, "data", "raw", "epidemiologia",
    "dengue_bolivia_semanal_SE01_13_2026.csv"
)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

OUT_CLIMA_DIARIO = os.path.join(PROCESSED_DIR, "clima_diario_imputado.csv")
OUT_CLIMA_SEMANAL = os.path.join(PROCESSED_DIR, "clima_semanal_calidad.csv")
OUT_DENGUE_MUN = os.path.join(PROCESSED_DIR, "dengue_municipal_validado.csv")
OUT_MALARIA_MUN = os.path.join(PROCESSED_DIR, "malaria_municipal_validado.csv")
OUT_DENGUE_SEM = os.path.join(PROCESSED_DIR, "dengue_semanal_validado.csv")
OUT_RESUMEN_MD = os.path.join(PROCESSED_DIR, "resumen_calidad_pipeline.md")
OUT_RESUMEN_JSON = os.path.join(PROCESSED_DIR, "resumen_calidad_pipeline.json")

VARIABLES_CLIMATICAS = ["temperatura_media", "humedad_media", "precipitacion_24h"]

# Columnas que no deben existir en ningun dataset epidemiologico (REQ-020).
COLUMNAS_PII_PROHIBIDAS = {
    "nombre", "apellido", "ci", "carnet", "documento", "direccion",
    "telefono", "paciente", "historia_clinica"
}


# ============================================================
# UTILIDADES
# ============================================================

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


# ============================================================
# PARTE 1: VALIDACION EPIDEMIOLOGICA (COM-xx / EPI-xx)
# ============================================================

def validar_sin_pii(df, nombre_dataset):
    columnas = {c.lower() for c in df.columns}
    interseccion = columnas & COLUMNAS_PII_PROHIBIDAS
    if interseccion:
        raise ValueError(
            f"EPI-05: {nombre_dataset} contiene columnas con posibles datos "
            f"personales: {interseccion}. El pipeline se detiene (REQ-020)."
        )


def validar_epidemiologia_municipal(df, columna_casos, nombre_dataset):
    """
    Aplica COM-01, COM-04, EPI-01 sobre un dataset acumulado municipal.
    No imputa: solo valida, marca y, si corresponde, rechaza.
    """

    datos = df.copy()

    validar_sin_pii(datos, nombre_dataset)

    datos["estado_calidad"] = "valido"
    datos["regla_aplicada"] = ""
    datos["motivo_qc"] = ""

    # COM-01: municipio vacio
    vacio = datos["municipio"].astype(str).str.strip().eq("")
    datos.loc[vacio, "estado_calidad"] = "rechazado"
    datos.loc[vacio, "regla_aplicada"] = "COM-01"
    datos.loc[vacio, "motivo_qc"] = "municipio_vacio"

    # COM-04: duplicado exacto de municipio+anio dentro del mismo lote
    duplicados = datos.duplicated(subset=["municipio", "anio"], keep="first")
    datos.loc[duplicados, "estado_calidad"] = "rechazado"
    datos.loc[duplicados, "regla_aplicada"] = "COM-04"
    datos.loc[duplicados, "motivo_qc"] = "duplicado_municipio_anio"

    # EPI-01: casos negativos o no enteros
    valores = pd.to_numeric(datos[columna_casos], errors="coerce")
    invalidos = valores.isna() | (valores < 0) | (valores % 1 != 0)
    datos.loc[invalidos, "estado_calidad"] = "rechazado"
    datos.loc[invalidos, "regla_aplicada"] = "EPI-01"
    datos.loc[invalidos, "motivo_qc"] = "casos_negativos_o_no_enteros"

    # Trazabilidad minima (seccion 3 de reglas_calidad_datos.md)
    datos["fuente"] = datos.get("fuente", "Ministerio de Salud y Deportes de Bolivia")
    datos["periodo_dato"] = datos.get("periodo", "SE 1-13")
    datos["version_lote"] = os.path.basename(nombre_dataset)

    return datos


def marcar_cobertura_municipal(dengue, malaria, catalogo_municipios):
    """
    Distingue 'sin_reporte' de 'cero_casos' para cada municipio del catalogo,
    en vez de asumir que la ausencia de una fila equivale a cero (regla 6.2.1
    y 6.2.2 de reglas_calidad_datos.md).
    """

    cobertura = pd.DataFrame({"municipio": sorted(catalogo_municipios)})

    dengue_municipios = set(dengue["municipio"])
    malaria_municipios = set(malaria["municipio"])

    cobertura["dengue_estado"] = cobertura["municipio"].apply(
        lambda m: "reportado" if m in dengue_municipios else "sin_reporte"
    )

    cobertura["malaria_estado"] = cobertura["municipio"].apply(
        lambda m: "reportado" if m in malaria_municipios else "sin_reporte"
    )

    return cobertura


def validar_dengue_semanal_nacional(df):
    """
    Serie semanal nacional. El propio boletin la marca como provisional en
    cada fila (nota de la fuente) -> estado_calidad = 'provisional', no
    'valido', siguiendo la regla 6.2.4.
    """

    datos = df.copy()
    validar_sin_pii(datos, "dengue_bolivia_semanal_SE01_13_2026.csv")

    datos["estado_calidad"] = "provisional"
    datos["regla_aplicada"] = "EPI-provisional"
    datos["motivo_qc"] = "fuente_declara_dato_provisional_sujeto_a_actualizacion"

    valores = pd.to_numeric(datos["casos_dengue"], errors="coerce")
    invalidos = valores.isna() | (valores < 0) | (valores % 1 != 0)
    datos.loc[invalidos, "estado_calidad"] = "rechazado"
    datos.loc[invalidos, "regla_aplicada"] = "EPI-01"
    datos.loc[invalidos, "motivo_qc"] = "casos_negativos_o_no_enteros"

    semana_invalida = ~datos["semana_epidemiologica"].between(1, 53)
    datos.loc[semana_invalida, "estado_calidad"] = "rechazado"
    datos.loc[semana_invalida, "regla_aplicada"] = "EPI-03"
    datos.loc[semana_invalida, "motivo_qc"] = "semana_epidemiologica_invalida"

    return datos


# ============================================================
# PARTE 2: CALENDARIO DIARIO GLOBAL (corrige riesgo de desfase)
# ============================================================

def construir_calendario_global(diario):
    """
    El reindexado anterior (documentado como riesgo conocido) se hacia por
    grupo/municipio, pudiendo generar un desfase de hasta 1 fila entre
    municipios. Aqui se usa un UNICO calendario global (union de fechas
    minima/maxima observadas en todo el dataset) para los cuatro municipios,
    de modo que todos comparten exactamente el mismo eje temporal.
    """

    diario = diario.copy()
    diario["fecha"] = pd.to_datetime(diario["fecha"])

    fecha_min = diario["fecha"].min()
    fecha_max = diario["fecha"].max()
    calendario = pd.date_range(fecha_min, fecha_max, freq="D")

    municipios = sorted(diario["municipio"].unique())

    indice_completo = pd.MultiIndex.from_product(
        [municipios, calendario], names=["municipio", "fecha"]
    )

    completo = (
        diario.set_index(["municipio", "fecha"])
        .reindex(indice_completo)
        .reset_index()
    )

    dias_esperados = len(calendario)

    return completo, dias_esperados, fecha_min, fecha_max


# ============================================================
# PARTE 3: IMPUTACION CLIMATICA (orden de reglas_calidad_datos.md §5.2)
# ============================================================

def calcular_vecino_mas_cercano(coordenadas):
    """
    coordenadas: dict municipio -> (lat, lon)
    Devuelve dict municipio -> municipio_vecino_mas_cercano.
    """

    vecinos = {}

    for municipio, (lat1, lon1) in coordenadas.items():
        mejor = None
        mejor_dist = None

        for otro, (lat2, lon2) in coordenadas.items():
            if otro == municipio:
                continue

            dist = haversine_km(lat1, lon1, lat2, lon2)

            if mejor_dist is None or dist < mejor_dist:
                mejor_dist = dist
                mejor = otro

        vecinos[municipio] = (mejor, mejor_dist)

    return vecinos


def imputar_variable(completo, variable, vecinos):
    """
    Aplica, en orden:
    1) interpolacion lineal para huecos internos de hasta 2 dias;
    2) mediana historica del mismo municipio y semana ISO (solo aplicable si
       hay mas de un anio de historia; con los datos actuales -un solo anio-
       se documenta como no aplicable en vez de forzarla);
    3) mediana del municipio vecino mas cercano, en la misma fecha;
    4) si nada de lo anterior resuelve el hueco, se deja como faltante.
    """

    completo[f"{variable}_original"] = completo[variable]
    completo[f"{variable}_metodo"] = "observado"
    completo.loc[completo[variable].isna(), f"{variable}_metodo"] = "faltante"

    resultado_por_municipio = []

    for municipio, grupo in completo.groupby("municipio"):
        grupo = grupo.sort_values("fecha").copy()

        antes = grupo[variable].isna()

        interpolado = grupo[variable].interpolate(
            method="linear", limit=2, limit_area="inside"
        )

        se_interpolo = antes & interpolado.notna()
        grupo[variable] = interpolado
        grupo.loc[se_interpolo, f"{variable}_metodo"] = "interpolacion_lineal"

        resultado_por_municipio.append(grupo)

    completo = pd.concat(resultado_por_municipio, ignore_index=True)

    # Paso 2 (mediana historica por semana del anio): no aplicable con un
    # unico anio de datos. Se deja constancia explicita, sin forzar el paso.
    anios_disponibles = completo["fecha"].dt.year.nunique()
    historia_suficiente = anios_disponibles > 1

    if historia_suficiente:
        completo["semana_iso"] = completo["fecha"].dt.isocalendar().week
        mediana_hist = (
            completo.groupby(["municipio", "semana_iso"])[variable]
            .transform("median")
        )
        aun_faltante = completo[variable].isna()
        completo.loc[aun_faltante, variable] = mediana_hist[aun_faltante]
        completo.loc[
            aun_faltante & completo[variable].notna(), f"{variable}_metodo"
        ] = "mediana_historica_municipio_semana"

    # Paso 3: mediana del municipio vecino mas cercano, misma fecha.
    aun_faltante = completo[variable].isna()

    if aun_faltante.any():
        tabla_vecino = completo.pivot_table(
            index="fecha", columns="municipio", values=variable
        )

        for idx in completo.index[aun_faltante]:
            municipio = completo.at[idx, "municipio"]
            fecha = completo.at[idx, "fecha"]
            vecino, _ = vecinos.get(municipio, (None, None))

            if vecino is None or fecha not in tabla_vecino.index:
                continue

            valor_vecino = tabla_vecino.at[fecha, vecino]

            if pd.notna(valor_vecino):
                completo.at[idx, variable] = valor_vecino
                completo.at[idx, f"{variable}_metodo"] = (
                    f"mediana_municipio_vecino({vecino})"
                )

    completo[f"{variable}_es_imputado"] = (
        completo[f"{variable}_metodo"] != "observado"
    ) & (completo[f"{variable}_metodo"] != "faltante")

    return completo, historia_suficiente


# ============================================================
# PARTE 4: REAGREGACION SEMANAL CON NIVEL DE CONFIANZA
# ============================================================

def reagregar_semanal_con_confianza(diario_imputado):
    datos = diario_imputado.copy()

    iso = datos["fecha"].dt.isocalendar()
    datos["anio"] = iso.year.astype(int)
    datos["semana_epidemiologica"] = iso.week.astype(int)

    agregaciones = {
        "temperatura_media": "mean",
        "humedad_media": "mean",
        "precipitacion_24h": "sum",
    }

    semanal = (
        datos.groupby(["municipio", "anio", "semana_epidemiologica"])
        .agg(
            **{
                "temperatura_media": ("temperatura_media", "mean"),
                "humedad_media": ("humedad_media", "mean"),
                "precipitacion_total_mm": ("precipitacion_24h", "sum"),
                "dias_en_semana": ("fecha", "count"),
                "dias_temperatura_imputados": (
                    "temperatura_media_es_imputado", "sum"
                ),
                "dias_humedad_imputados": ("humedad_media_es_imputado", "sum"),
                "dias_precipitacion_imputados": (
                    "precipitacion_24h_es_imputado", "sum"
                ),
                "dias_faltantes": (
                    "temperatura_media",
                    lambda s: s.isna().sum(),
                ),
            }
        )
        .reset_index()
    )

    semanal = semanal[semanal["semana_epidemiologica"].between(1, 13)].copy()

    semanal["porcentaje_faltante"] = (
        semanal["dias_faltantes"] / semanal["dias_en_semana"] * 100
    ).round(2)

    def clasificar(pct):
        if pct <= 5:
            return "confianza_normal"
        if pct <= 20:
            return "confianza_baja"
        return "datos_insuficientes"

    semanal["nivel_confianza"] = semanal["porcentaje_faltante"].apply(clasificar)

    return semanal


# ============================================================
# PARTE 5: RESUMEN DE CALIDAD (seccion 7 de reglas_calidad_datos.md)
# ============================================================

def construir_resumen(
    dengue_val, malaria_val, dengue_sem_val, cobertura_municipal,
    semanal_confianza, historia_suficiente, dias_esperados,
):
    resumen = {}

    resumen["epidemiologia"] = {
        "dengue_municipal": {
            "recibidos": len(dengue_val),
            "validos": int((dengue_val["estado_calidad"] == "valido").sum()),
            "rechazados": int((dengue_val["estado_calidad"] == "rechazado").sum()),
        },
        "malaria_municipal": {
            "recibidos": len(malaria_val),
            "validos": int((malaria_val["estado_calidad"] == "valido").sum()),
            "rechazados": int((malaria_val["estado_calidad"] == "rechazado").sum()),
        },
        "dengue_semanal_nacional": {
            "recibidos": len(dengue_sem_val),
            "provisionales": int(
                (dengue_sem_val["estado_calidad"] == "provisional").sum()
            ),
            "rechazados": int(
                (dengue_sem_val["estado_calidad"] == "rechazado").sum()
            ),
        },
        "municipios_sin_reporte_dengue": cobertura_municipal.loc[
            cobertura_municipal["dengue_estado"] == "sin_reporte", "municipio"
        ].tolist(),
        "municipios_sin_reporte_malaria": cobertura_municipal.loc[
            cobertura_municipal["malaria_estado"] == "sin_reporte", "municipio"
        ].tolist(),
    }

    resumen["clima"] = {
        "dias_esperados_calendario_global": int(dias_esperados),
        "mediana_historica_por_semana_aplicable": historia_suficiente,
        "municipios_por_nivel_confianza": (
            semanal_confianza.groupby("nivel_confianza")["municipio"]
            .apply(lambda s: sorted(s.unique().tolist()))
            .to_dict()
        ),
        "semanas_datos_insuficientes": semanal_confianza.loc[
            semanal_confianza["nivel_confianza"] == "datos_insuficientes",
            ["municipio", "semana_epidemiologica"],
        ].to_dict(orient="records"),
    }

    resumen["reglas_no_aplicables_con_datos_actuales"] = [
        "Mediana historica por semana del anio (5.2, paso 2): requiere mas "
        "de un anio de observaciones; el dataset actual solo cubre 2026."
        if not historia_suficiente else None
    ]
    resumen["reglas_no_aplicables_con_datos_actuales"] = [
        r for r in resumen["reglas_no_aplicables_con_datos_actuales"] if r
    ]

    return resumen


# ============================================================
# MAIN
# ============================================================

def main():
    inicio = pd.Timestamp.now()

    print("\n==========================================")
    print("PIPELINE DE LIMPIEZA, VALIDACION E IMPUTACION")
    print("==========================================")

    # --------------------------------------------------------
    # 1. VALIDACION EPIDEMIOLOGICA
    # --------------------------------------------------------

    print("\n[1/5] Validando datos epidemiologicos...")

    dengue = pd.read_csv(DENGUE_MUNICIPAL)
    malaria = pd.read_csv(MALARIA_MUNICIPAL)
    dengue_sem = pd.read_csv(DENGUE_SEMANAL_NACIONAL)

    for df in (dengue, malaria):
        df["municipio"] = df["municipio"].astype(str).str.strip().str.upper()

    dengue_val = validar_epidemiologia_municipal(
        dengue, "casos_dengue_acumulados_se1_13", DENGUE_MUNICIPAL
    )
    malaria_val = validar_epidemiologia_municipal(
        malaria, "total_malaria", MALARIA_MUNICIPAL
    )
    dengue_sem_val = validar_dengue_semanal_nacional(dengue_sem)

    catalogo_municipios = set(dengue_val["municipio"]) | set(malaria_val["municipio"])
    cobertura_municipal = marcar_cobertura_municipal(
        dengue_val, malaria_val, catalogo_municipios
    )

    dengue_val.to_csv(OUT_DENGUE_MUN, index=False, encoding="utf-8-sig")
    malaria_val.to_csv(OUT_MALARIA_MUN, index=False, encoding="utf-8-sig")
    dengue_sem_val.to_csv(OUT_DENGUE_SEM, index=False, encoding="utf-8-sig")

    print(
        "Dengue municipal:", len(dengue_val), "filas |",
        int((dengue_val["estado_calidad"] == "rechazado").sum()), "rechazadas"
    )
    print(
        "Malaria municipal:", len(malaria_val), "filas |",
        int((malaria_val["estado_calidad"] == "rechazado").sum()), "rechazadas"
    )
    print(
        "Dengue semanal nacional:", len(dengue_sem_val), "filas |",
        "todas provisionales por declaracion de la fuente"
    )

    # --------------------------------------------------------
    # 2. CALENDARIO GLOBAL
    # --------------------------------------------------------

    print("\n[2/5] Reconstruyendo calendario diario global...")

    diario_adriana = pd.read_csv(CLIMA_DIARIO_ADRIANA)
    completo, dias_esperados, fecha_min, fecha_max = construir_calendario_global(
        diario_adriana
    )

    print(
        f"Calendario global: {fecha_min.date()} a {fecha_max.date()} "
        f"({dias_esperados} dias) x {completo['municipio'].nunique()} municipios "
        f"= {len(completo)} filas esperadas."
    )

    huecos_por_municipio = (
        completo.groupby("municipio")["temperatura_media"]
        .apply(lambda s: s.isna().sum())
    )
    print("Dias sin observacion antes de imputar:")
    print(huecos_por_municipio.to_string())

    # --------------------------------------------------------
    # 3. IMPUTACION CLIMATICA
    # --------------------------------------------------------

    print("\n[3/5] Imputando variables climaticas segun reglas_calidad_datos.md...")

    raw = pd.read_csv(RAW_SENAMHI)
    coordenadas = (
        raw.groupby("municipio")[["latitud", "longitud"]].mean().apply(tuple, axis=1)
        .to_dict()
    )
    vecinos = calcular_vecino_mas_cercano(coordenadas)

    print("Municipio vecino mas cercano usado como respaldo de imputacion:")
    for m, (v, d) in vecinos.items():
        print(f"  {m} -> {v} ({d:.1f} km)")

    historia_suficiente = False
    for variable in VARIABLES_CLIMATICAS:
        completo, historia_suficiente = imputar_variable(completo, variable, vecinos)

    for variable in VARIABLES_CLIMATICAS:
        conteo = completo[f"{variable}_metodo"].value_counts()
        print(f"\nMetodo aplicado para {variable}:")
        print(conteo.to_string())

    completo.to_csv(OUT_CLIMA_DIARIO, index=False, encoding="utf-8-sig")

    # --------------------------------------------------------
    # 4. REAGREGACION SEMANAL CON CONFIANZA
    # --------------------------------------------------------

    print("\n[4/5] Reagregando a nivel semanal con nivel de confianza...")

    semanal_confianza = reagregar_semanal_con_confianza(completo)
    semanal_confianza.to_csv(OUT_CLIMA_SEMANAL, index=False, encoding="utf-8-sig")

    print(
        semanal_confianza[
            ["municipio", "semana_epidemiologica", "porcentaje_faltante",
             "nivel_confianza"]
        ].to_string(index=False)
    )

    resumen_confianza = semanal_confianza["nivel_confianza"].value_counts()
    print("\nDistribucion de semanas por nivel de confianza:")
    print(resumen_confianza.to_string())

    # --------------------------------------------------------
    # 5. RESUMEN DE CALIDAD
    # --------------------------------------------------------

    print("\n[5/5] Generando resumen de calidad del lote...")

    resumen = construir_resumen(
        dengue_val, malaria_val, dengue_sem_val, cobertura_municipal,
        semanal_confianza, historia_suficiente, dias_esperados,
    )

    with open(OUT_RESUMEN_JSON, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)

    duracion = (pd.Timestamp.now() - inicio).total_seconds()

    with open(OUT_RESUMEN_MD, "w", encoding="utf-8") as f:
        f.write("# Resumen de calidad del pipeline de datos\n\n")
        f.write(f"Generado: {pd.Timestamp.now().isoformat()}\n\n")
        f.write(f"Duracion de ejecucion: {duracion:.2f} segundos\n\n")
        f.write("## Epidemiologia\n\n")
        f.write("```json\n" + json.dumps(
            resumen["epidemiologia"], ensure_ascii=False, indent=2
        ) + "\n```\n\n")
        f.write("## Clima\n\n")
        f.write("```json\n" + json.dumps(
            resumen["clima"], ensure_ascii=False, indent=2, default=str
        ) + "\n```\n\n")
        f.write("## Reglas no aplicables con los datos actuales\n\n")
        for regla in resumen["reglas_no_aplicables_con_datos_actuales"]:
            f.write(f"- {regla}\n")

    print("\n==========================================")
    print("PIPELINE COMPLETADO EN {:.2f} SEGUNDOS".format(duracion))
    print("==========================================")
    print("\nArchivos generados:")
    for ruta in (
        OUT_DENGUE_MUN, OUT_MALARIA_MUN, OUT_DENGUE_SEM,
        OUT_CLIMA_DIARIO, OUT_CLIMA_SEMANAL,
        OUT_RESUMEN_MD, OUT_RESUMEN_JSON,
    ):
        print(" -", ruta)


if __name__ == "__main__":
    main()
