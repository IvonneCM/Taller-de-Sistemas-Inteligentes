"""
EDA epidemiológico inicial
Sistema de Predicción Temprana de Brotes de Dengue y Malaria

Fuente:
Ministerio de Salud y Deportes de Bolivia
Boletín Epidemiológico N° 13 - 2026

IMPORTANTE:
Este análisis utiliza únicamente datos epidemiológicos reales.
No se generan datos sintéticos.

El análisis climático con SENAMHI se realizará posteriormente.
"""

import os
import json
import unicodedata
import urllib.request

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import squarify
from matplotlib.patches import Polygon


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

GEOJSON_URL = (
    "https://github.com/YoViajo/geodatos/raw/refs/heads/master/"
    "limites/bol_lim_dpto.json"
)
GEOJSON_CACHE = os.path.join(OUTPUT_DIR, "bol_lim_dpto.json")

DEPARTAMENTOS_BOLIVIA = {
    "BENI", "CHUQUISACA", "COCHABAMBA", "LA PAZ", "ORURO",
    "PANDO", "POTOSI", "SANTA CRUZ", "TARIJA",
}


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
        dengue_municipal["casos_dengue_acumulados_se1_13"].sum()
    )

    total_malaria = malaria["total_malaria"].sum()

    print("Dengue semanal:", total_dengue)
    print("Dengue municipal:", total_dengue_municipal)
    print("Malaria:", total_malaria)

    esperado_dengue = 341
    esperado_malaria = 1615

    if total_dengue != esperado_dengue or total_dengue_municipal != esperado_dengue:
        print(
            f"AVISO: el total de dengue no coincide exactamente con el "
            f"boletín ({esperado_dengue}). Revisar antes de la defensa."
        )
    if total_malaria != esperado_malaria:
        print(
            f"AVISO: el total de malaria no coincide exactamente con el "
            f"boletín ({esperado_malaria}). Revisar antes de la defensa."
        )

    if (
        total_dengue == esperado_dengue
        and total_dengue_municipal == esperado_dengue
        and total_malaria == esperado_malaria
    ):
        print("\n✓ Los totales coinciden con el boletín oficial.")


# ============================================================
# CALIDAD DE DATOS
# ============================================================

def analizar_calidad(dengue_semanal, dengue_municipal, malaria):

    resultados = []

    datasets = {
        "Dengue semanal": dengue_semanal,
        "Dengue municipal": dengue_municipal,
        "Malaria municipal": malaria,
    }

    for nombre, df in datasets.items():

        resultados.append({
            "dataset": nombre,
            "filas": len(df),
            "columnas": len(df.columns),
            "valores_faltantes": int(df.isnull().sum().sum()),
            "duplicados": int(df.duplicated().sum()),
        })

    calidad = pd.DataFrame(resultados)

    calidad.to_csv(
        os.path.join(OUTPUT_DIR, "calidad_datos.csv"),
        index=False,
    )

    print("\n========== CALIDAD DE DATOS ==========")
    print(calidad.to_string(index=False))

    analizar_observaciones(dengue_municipal, malaria)


def analizar_observaciones(dengue_municipal, malaria):
    """El boletín trae una columna de observaciones documentando
    ambigüedades del PDF fuente (ej. celdas vacías). Contar cuántos
    municipios tienen alguna nota es en sí mismo un indicador de
    calidad de datos que la defensa puede citar."""

    filas = []
    for nombre, df in [("Dengue municipal", dengue_municipal), ("Malaria municipal", malaria)]:
        if "observaciones" not in df.columns:
            continue
        con_nota = df["observaciones"].notna().sum()
        filas.append({
            "dataset": nombre,
            "municipios_con_observacion": int(con_nota),
            "total_municipios": len(df),
            "pct_con_observacion": round(100 * con_nota / len(df), 1) if len(df) else 0,
        })

    if not filas:
        return

    resumen = pd.DataFrame(filas)
    resumen.to_csv(os.path.join(OUTPUT_DIR, "calidad_observaciones.csv"), index=False)
    print("\n--- Municipios con observación de calidad de datos en el boletín ---")
    print(resumen.to_string(index=False))


# ============================================================
# ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

def generar_resumenes(dengue_semanal, dengue_municipal, malaria):

    dengue_semanal.describe().to_csv(
        os.path.join(OUTPUT_DIR, "resumen_dengue_semanal.csv")
    )

    dengue_municipal.describe().to_csv(
        os.path.join(OUTPUT_DIR, "resumen_dengue_municipal.csv")
    )

    malaria.describe().to_csv(
        os.path.join(OUTPUT_DIR, "resumen_malaria.csv")
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

    return df[(df[columna] < limite_inferior) | (df[columna] > limite_superior)]


def analizar_outliers(dengue_municipal, malaria):

    outliers_dengue = detectar_outliers(dengue_municipal, "casos_dengue_acumulados_se1_13")
    outliers_malaria = detectar_outliers(malaria, "total_malaria")

    outliers_dengue.to_csv(os.path.join(OUTPUT_DIR, "outliers_dengue.csv"), index=False)
    outliers_malaria.to_csv(os.path.join(OUTPUT_DIR, "outliers_malaria.csv"), index=False)

    print("\n========== OUTLIERS ==========")
    print("Municipios atípicos dengue:", len(outliers_dengue))
    print("Municipios atípicos malaria:", len(outliers_malaria))


# ============================================================
# SERIE TEMPORAL + ACUMULADO (DENGUE)
# ============================================================

def grafico_dengue_semanal(df):

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(df["semana_epidemiologica"], df["casos_dengue"], marker="o", color="tab:red", label="Casos semanales")
    ax1.set_xlabel("Semana epidemiológica")
    ax1.set_ylabel("Casos semanales", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_xticks(df["semana_epidemiologica"])
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(df["semana_epidemiologica"], df["casos_dengue"].cumsum(), color="tab:blue", linestyle="--", label="Acumulado")
    ax2.set_ylabel("Casos acumulados", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    plt.title("Casos de dengue por semana epidemiológica\nBolivia - SE 1 a SE 13, 2026")
    fig.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "dengue_serie_temporal.png"), dpi=300)
    plt.close()


# ============================================================
# TOP N MUNICIPIOS (BARRAS CON GRADIENTE DE COLOR)
# ============================================================

def grafico_top_municipios(df, columna, titulo, archivo, top_n=15, color_map="Reds"):

    datos = df.nlargest(top_n, columna).sort_values(columna, ascending=True)
    cmap = plt.get_cmap(color_map)
    norm = mcolors.Normalize(vmin=datos[columna].min(), vmax=datos[columna].max())
    colores = [cmap(norm(v)) for v in datos[columna]]

    plt.figure(figsize=(10, 8))
    plt.barh(datos["municipio"], datos[columna], color=colores, edgecolor="black", linewidth=0.4)
    plt.title(titulo)
    plt.xlabel("Casos acumulados")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, archivo), dpi=300)
    plt.close()


# ============================================================
# TREEMAPS (proporción de casos por municipio)
# ============================================================

def grafico_treemap(df, columna, titulo, archivo, top_n=20, color_map="OrRd"):

    datos = df.nlargest(top_n, columna).copy()
    resto = df[columna].sum() - datos[columna].sum()
    if resto > 0:
        datos = pd.concat([
            datos,
            pd.DataFrame([{"municipio": f"Otros ({len(df) - top_n} municipios)", columna: resto}]),
        ], ignore_index=True)

    cmap = plt.get_cmap(color_map)
    norm = mcolors.Normalize(vmin=datos[columna].min(), vmax=datos[columna].max())
    colores = [cmap(norm(v)) for v in datos[columna]]
    etiquetas = [f"{m}\n{v:.0f}" for m, v in zip(datos["municipio"], datos[columna])]

    plt.figure(figsize=(12, 7))
    squarify.plot(sizes=datos[columna], label=etiquetas, color=colores, edgecolor="white", text_kwargs={"fontsize": 8})
    plt.title(titulo)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, archivo), dpi=300)
    plt.close()


# ============================================================
# MALARIA POR ESPECIE (BARRA + PASTEL)
# ============================================================

def grafico_malaria_especie(df):

    especies = {
        "P. vivax": df["p_vivax"].sum(),
        "P. falciparum": df["p_falciparum"].sum(),
        "Mixta": df["mixta"].sum(),
    }

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(especies.keys(), especies.values(), color=["#4c72b0", "#dd8452", "#55a868"])
    axes[0].set_title("Casos de malaria según especie")
    axes[0].set_ylabel("Número de casos")

    axes[1].pie(especies.values(), labels=especies.keys(), autopct="%1.1f%%",
                colors=["#4c72b0", "#dd8452", "#55a868"], startangle=90)
    axes[1].set_title("Proporción por especie")

    fig.suptitle("Malaria por especie — Bolivia, SE 1-13, 2026")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "malaria_por_especie.png"), dpi=300)
    plt.close()


# ============================================================
# DISTRIBUCIONES
# ============================================================

def grafico_distribuciones(dengue_municipal, malaria):

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].hist(dengue_municipal["casos_dengue_acumulados_se1_13"], bins=10, edgecolor="black", color="tab:red", alpha=0.8)
    axes[0].set_title("Distribución de casos de dengue por municipio")
    axes[0].set_xlabel("Casos acumulados")
    axes[0].set_ylabel("Número de municipios")

    axes[1].hist(malaria["total_malaria"], bins=10, edgecolor="black", color="tab:green", alpha=0.8)
    axes[1].set_title("Distribución de casos de malaria por municipio")
    axes[1].set_xlabel("Casos acumulados")
    axes[1].set_ylabel("Número de municipios")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "distribucion_variables.png"), dpi=300)
    plt.close()


# ============================================================
# COMPARACIÓN DENGUE VS. MALARIA POR MUNICIPIO
# ============================================================

def grafico_comparacion_dengue_malaria(dengue_municipal, malaria):

    comparacion = dengue_municipal.merge(
        malaria, on="municipio", how="inner", suffixes=("_dengue", "_malaria")
    )

    if comparacion.empty:
        print("\nNo hay municipios en común entre dengue y malaria para comparar.")
        return

    plt.figure(figsize=(7, 6))
    plt.scatter(
        comparacion["casos_dengue_acumulados_se1_13"],
        comparacion["total_malaria"],
        alpha=0.7, edgecolor="black", s=60,
    )
    for _, fila in comparacion.iterrows():
        plt.annotate(fila["municipio"], (fila["casos_dengue_acumulados_se1_13"], fila["total_malaria"]),
                     fontsize=7, alpha=0.8, xytext=(3, 3), textcoords="offset points")

    plt.title("Dengue vs. malaria — municipios con ambas enfermedades reportadas")
    plt.xlabel("Casos acumulados de dengue")
    plt.ylabel("Casos acumulados de malaria")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "comparacion_dengue_malaria.png"), dpi=300)
    plt.close()

    print(f"\nMunicipios con dengue y malaria reportados simultáneamente: {len(comparacion)}")


def grafico_ranking_combinado(dengue_municipal, malaria, top_n=10):

    dengue_tot = dengue_municipal.groupby("municipio")["casos_dengue_acumulados_se1_13"].sum()
    malaria_tot = malaria.groupby("municipio")["total_malaria"].sum()

    combinado = pd.concat([dengue_tot, malaria_tot], axis=1).fillna(0)
    combinado.columns = ["dengue", "malaria"]
    combinado["total"] = combinado["dengue"] + combinado["malaria"]
    top = combinado.nlargest(top_n, "total").sort_values("total", ascending=True)

    plt.figure(figsize=(10, 7))
    plt.barh(top.index, top["dengue"], label="Dengue", color="tab:red")
    plt.barh(top.index, top["malaria"], left=top["dengue"], label="Malaria", color="tab:green")
    plt.title(f"Top {top_n} municipios — dengue + malaria combinados")
    plt.xlabel("Casos acumulados")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "ranking_combinado_municipios.png"), dpi=300)
    plt.close()


# ============================================================
# MAPA POR DEPARTAMENTO (CHOROPLETH, SIN GEOPANDAS)
# ============================================================

def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


def _descargar_geojson_departamentos():
    if not os.path.exists(GEOJSON_CACHE):
        print("Descargando límites departamentales de Bolivia (una sola vez)...")
        urllib.request.urlretrieve(GEOJSON_URL, GEOJSON_CACHE)
    with open(GEOJSON_CACHE, encoding="utf-8") as f:
        return json.load(f)


def _encontrar_campo_nombre(geojson):
    mejor_campo, mejor_match = None, -1
    props_ejemplo = geojson["features"][0]["properties"]
    for campo in props_ejemplo:
        valores = {_sin_tildes(f["properties"].get(campo, "")) for f in geojson["features"]}
        matches = len(valores & DEPARTAMENTOS_BOLIVIA)
        if matches > mejor_match:
            mejor_match, mejor_campo = matches, campo
    return mejor_campo


def dibujar_mapa_departamentos(datos_por_departamento: dict, titulo: str, archivo_salida: str, etiqueta_barra: str):

    try:
        geojson = _descargar_geojson_departamentos()
    except Exception as e:
        print(f"\nNo se pudo generar el mapa por departamento (sin conexión o URL caída): {e}")
        return

    campo_nombre = _encontrar_campo_nombre(geojson)
    datos_norm = {_sin_tildes(k): v for k, v in datos_por_departamento.items()}
    valores_validos = [v for v in datos_norm.values() if v is not None]
    if not valores_validos:
        print(f"\nNo hay datos válidos para el mapa: {titulo}")
        return

    cmap = plt.get_cmap("OrRd")
    norm = mcolors.Normalize(vmin=min(valores_validos), vmax=max(valores_validos))

    fig, ax = plt.subplots(figsize=(8, 9))
    for feature in geojson["features"]:
        nombre = _sin_tildes(feature["properties"].get(campo_nombre, ""))
        valor = datos_norm.get(nombre)
        color = cmap(norm(valor)) if valor is not None else "#e0e0e0"

        geom = feature["geometry"]
        poligonos = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poligono in poligonos:
            anillo_externo = poligono[0]
            ax.add_patch(Polygon(anillo_externo, closed=True, facecolor=color, edgecolor="black", linewidth=0.6))

        if valor is not None:
            xs = [p[0] for poly in poligonos for p in poly[0]]
            ys = [p[1] for poly in poligonos for p in poly[0]]
            ax.annotate(f"{feature['properties'].get(campo_nombre, '')}\n{valor:.0f}",
                        (sum(xs) / len(xs), sum(ys) / len(ys)),
                        ha="center", fontsize=7, weight="bold")

    ax.autoscale()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titulo)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label=etiqueta_barra, shrink=0.7)

    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300)
    plt.close()


def generar_mapas_departamento(dengue_municipal, malaria):

    if "departamento" not in dengue_municipal.columns or "departamento" not in malaria.columns:
        print("\nNo hay columna 'departamento' en los datos: se omiten los mapas.")
        return

    dengue_por_dpto = dengue_municipal.groupby("departamento")["casos_dengue_acumulados_se1_13"].sum().to_dict()
    malaria_por_dpto = malaria.groupby("departamento")["total_malaria"].sum().to_dict()

    dibujar_mapa_departamentos(
        dengue_por_dpto,
        "Casos acumulados de dengue por departamento\nBolivia, SE 1-13, 2026",
        os.path.join(OUTPUT_DIR, "mapa_dengue_departamento.png"),
        "Casos de dengue",
    )
    dibujar_mapa_departamentos(
        malaria_por_dpto,
        "Casos acumulados de malaria por departamento\nBolivia, SE 1-13, 2026",
        os.path.join(OUTPUT_DIR, "mapa_malaria_departamento.png"),
        "Casos de malaria",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nEDA EPIDEMIOLÓGICO - DENGUE Y MALARIA")
    print("Fuente: Ministerio de Salud y Deportes de Bolivia - Boletín N°13, 2026")

    dengue_semanal, dengue_municipal, malaria = cargar_datos()

    validar_datos(dengue_semanal, dengue_municipal, malaria)
    analizar_calidad(dengue_semanal, dengue_municipal, malaria)
    generar_resumenes(dengue_semanal, dengue_municipal, malaria)
    analizar_outliers(dengue_municipal, malaria)

    grafico_dengue_semanal(dengue_semanal)

    grafico_top_municipios(
        dengue_municipal, "casos_dengue_acumulados_se1_13",
        "Top 15 municipios — casos acumulados de dengue\nSE 1-13, Bolivia 2026",
        "dengue_top_municipios.png", color_map="Reds",
    )
    grafico_top_municipios(
        malaria, "total_malaria",
        "Top 15 municipios — casos acumulados de malaria\nSE 1-13, Bolivia 2026",
        "malaria_top_municipios.png", color_map="Greens",
    )

    grafico_treemap(
        dengue_municipal, "casos_dengue_acumulados_se1_13",
        "Proporción de casos de dengue por municipio (top 20)",
        "dengue_treemap.png", color_map="Reds",
    )
    grafico_treemap(
        malaria, "total_malaria",
        "Proporción de casos de malaria por municipio (top 20)",
        "malaria_treemap.png", color_map="Greens",
    )

    grafico_malaria_especie(malaria)
    grafico_distribuciones(dengue_municipal, malaria)
    grafico_comparacion_dengue_malaria(dengue_municipal, malaria)
    grafico_ranking_combinado(dengue_municipal, malaria)
    generar_mapas_departamento(dengue_municipal, malaria)

    print("\n✓ EDA completado.")
    print("Resultados guardados en:", OUTPUT_DIR)


if __name__ == "__main__":
    main()