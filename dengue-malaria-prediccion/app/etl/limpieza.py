"""
Modulo de limpieza e imputacion (TASK-010 / REQ-013, NFR-007).

Formaliza dentro del backend el prototipo que ya existia FUERA de el y que
ya fue probado sobre datos reales en Linea Base - Paso 2
(`scripts/limpieza_datos.py`, responsable: Tania Perez). Confirmado (ver
CONTEXT.md, divergencia registrada y resuelta el 2026-10-25): el prototipo
SI esta subido al repositorio — la nota de CONTEXT.md sobre el bloqueo de
DVC se referia a `data/raw/`, no al script, que no depende de DVC. Por eso
esta tarea reutiliza esa logica (orden de imputacion de
docs/reglas_calidad_datos.md §5.2) en vez de redisenarla desde cero, tal
como pide la nota de la propia tarea en tasks.md.

Alcance de REQ-013/NFR-007 que cubre este modulo:
1. Interpolacion temporal para datos climaticos faltantes (nunca para casos
   epidemiologicos — regla 2 de CLAUDE.md y principio 2 de
   reglas_calidad_datos.md: "no interpretar un dato ausente como cero").
2. Marcado de `es_dato_imputado` por fila.
3. Calculo del porcentaje de datos faltantes por municipio/ventana y su
   nivel de confianza asociado (umbrales de NFR-007 / design.md §5: <=5%
   normal, 5-20% confianza baja, >20% datos insuficientes — no se publica
   prediccion operativa).
"""

from __future__ import annotations

import math

import pandas as pd

UMBRAL_CONFIANZA_NORMAL_PCT = 5.0
UMBRAL_DATOS_INSUFICIENTES_PCT = 20.0

VARIABLES_CLIMATICAS = ["temperatura_media_c", "humedad_relativa_pct", "precipitacion_mm"]


# ============================================================
# Vecino mas cercano (reutilizado de scripts/limpieza_datos.py)
# ============================================================

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def vecino_mas_cercano(coordenadas: dict[str, tuple[float, float]]) -> dict[str, tuple[str | None, float | None]]:
    """coordenadas: {municipio: (lat, lon)}. Devuelve {municipio: (vecino, distancia_km)}."""
    vecinos: dict[str, tuple[str | None, float | None]] = {}
    for municipio, (lat1, lon1) in coordenadas.items():
        mejor, mejor_dist = None, None
        for otro, (lat2, lon2) in coordenadas.items():
            if otro == municipio:
                continue
            dist = haversine_km(lat1, lon1, lat2, lon2)
            if mejor_dist is None or dist < mejor_dist:
                mejor, mejor_dist = otro, dist
        vecinos[municipio] = (mejor, mejor_dist)
    return vecinos


# ============================================================
# Porcentaje de faltantes y nivel de confianza (NFR-007)
# ============================================================

def calcular_porcentaje_faltante(serie: pd.Series) -> float:
    if len(serie) == 0:
        return 0.0
    return round(serie.isna().sum() / len(serie) * 100, 2)


def nivel_confianza(porcentaje_faltante: float) -> str:
    if porcentaje_faltante <= UMBRAL_CONFIANZA_NORMAL_PCT:
        return "confianza_normal"
    if porcentaje_faltante <= UMBRAL_DATOS_INSUFICIENTES_PCT:
        return "confianza_baja"
    return "datos_insuficientes"


# ============================================================
# Calendario diario global (reutilizado de scripts/limpieza_datos.py)
# ============================================================

def construir_calendario_global(df: pd.DataFrame) -> pd.DataFrame:
    """Reindexa el DataFrame a un UNICO calendario diario (union de fechas
    minima/maxima observadas) compartido por todos los municipios, para que
    un dia sin ninguna fila (ausencia real, no un NaN explicito) tambien
    cuente como faltante. Sin este paso, `calcular_porcentaje_faltante`
    subestima los huecos reales (ver README.md: 27 dias ausentes en San
    Buenaventura, 21 en Palos Blancos, que no vienen como NaN sino como
    filas inexistentes)."""

    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])

    calendario = pd.date_range(datos["fecha"].min(), datos["fecha"].max(), freq="D")
    municipios = sorted(datos["municipio"].unique())
    indice_completo = pd.MultiIndex.from_product(
        [municipios, calendario], names=["municipio", "fecha"]
    )

    return (
        datos.set_index(["municipio", "fecha"])
        .reindex(indice_completo)
        .reset_index()
    )


# ============================================================
# Imputacion climatica (orden de reglas_calidad_datos.md §5.2)
# ============================================================

def imputar_variable(
    df: pd.DataFrame, variable: str, vecinos: dict[str, tuple[str | None, float | None]]
) -> pd.DataFrame:
    """Aplica, en orden, sobre una columna climatica:
    1) interpolacion lineal interna (huecos de hasta 2 periodos);
    2) mediana historica del mismo municipio y semana ISO, solo si hay mas
       de un anio de historia (si no, se documenta como no aplicable, nunca
       se fuerza);
    3) mediana del municipio vecino mas cercano, en la misma fecha;
    4) si nada resuelve el hueco, se conserva como faltante (NUNCA se
       inventa un valor fuera de esta cadena).

    Requiere columnas: municipio, fecha, <variable>. Agrega
    `{variable}_metodo` y `{variable}_es_imputado`.
    """

    datos = df.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"])

    datos[f"{variable}_metodo"] = "observado"
    datos.loc[datos[variable].isna(), f"{variable}_metodo"] = "faltante"

    # 1) interpolacion lineal por municipio
    partes = []
    for municipio, grupo in datos.groupby("municipio"):
        grupo = grupo.sort_values("fecha").copy()
        antes = grupo[variable].isna()
        interpolado = grupo[variable].interpolate(method="linear", limit=2, limit_area="inside")
        se_interpolo = antes & interpolado.notna()
        grupo[variable] = interpolado
        grupo.loc[se_interpolo, f"{variable}_metodo"] = "interpolacion_lineal"
        partes.append(grupo)
    datos = pd.concat(partes, ignore_index=True)

    # 2) mediana historica municipio+semana ISO (requiere >1 anio de datos)
    anios_disponibles = datos["fecha"].dt.year.nunique()
    historia_suficiente = anios_disponibles > 1
    if historia_suficiente:
        datos["semana_iso"] = datos["fecha"].dt.isocalendar().week
        mediana_hist = datos.groupby(["municipio", "semana_iso"])[variable].transform("median")
        aun_faltante = datos[variable].isna()
        datos.loc[aun_faltante, variable] = mediana_hist[aun_faltante]
        datos.loc[
            aun_faltante & datos[variable].notna(), f"{variable}_metodo"
        ] = "mediana_historica_municipio_semana"

    # 3) mediana del municipio vecino mas cercano, misma fecha
    aun_faltante = datos[variable].isna()
    if aun_faltante.any():
        tabla = datos.pivot_table(index="fecha", columns="municipio", values=variable)
        for idx in datos.index[aun_faltante]:
            municipio = datos.at[idx, "municipio"]
            fecha = datos.at[idx, "fecha"]
            vecino, _ = vecinos.get(municipio, (None, None))
            if vecino is None or fecha not in tabla.index:
                continue
            valor_vecino = tabla.at[fecha, vecino]
            if pd.notna(valor_vecino):
                datos.at[idx, variable] = valor_vecino
                datos.at[idx, f"{variable}_metodo"] = f"mediana_municipio_vecino({vecino})"

    # 4) lo que no se resolvio queda como faltante (metodo ya dice 'faltante')
    datos[f"{variable}_es_imputado"] = ~datos[f"{variable}_metodo"].isin(["observado", "faltante"])

    return datos


def imputar_y_marcar_clima(
    df: pd.DataFrame,
    coordenadas: dict[str, tuple[float, float]],
    variables: list[str] | None = None,
) -> pd.DataFrame:
    """Punto de entrada principal de TASK-010 para clima: imputa todas las
    variables climaticas y agrega `es_dato_imputado` (True si CUALQUIER
    variable de la fila fue imputada), consistente con la columna de
    `datos_climaticos` (un solo flag booleano por fila)."""

    variables = variables or VARIABLES_CLIMATICAS
    vecinos = vecino_mas_cercano(coordenadas)

    resultado = construir_calendario_global(df)
    for variable in variables:
        if variable not in resultado.columns:
            continue
        resultado = imputar_variable(resultado, variable, vecinos)

    columnas_imputado = [f"{v}_es_imputado" for v in variables if f"{v}_es_imputado" in resultado.columns]
    if columnas_imputado:
        resultado["es_dato_imputado"] = resultado[columnas_imputado].any(axis=1)
    else:
        resultado["es_dato_imputado"] = False

    return resultado


def resumen_calidad_por_municipio(
    df: pd.DataFrame, variable: str = "temperatura_media_c"
) -> pd.DataFrame:
    """Porcentaje de faltantes y nivel de confianza por municipio, ANTES de
    imputar (para que el porcentaje refleje la cobertura real recibida, no
    lo que se logro rellenar despues)."""

    df_calendario = construir_calendario_global(df)

    filas = []
    for municipio, grupo in df_calendario.groupby("municipio"):
        pct = calcular_porcentaje_faltante(grupo[variable])
        filas.append(
            {
                "municipio": municipio,
                "porcentaje_faltante": pct,
                "nivel_confianza": nivel_confianza(pct),
            }
        )
    return pd.DataFrame(filas)
