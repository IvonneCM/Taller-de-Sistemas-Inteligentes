"""
Validador del contrato de datos (docs/contrato_esquema_datos_procesados.md)
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Comprueba que los paneles que consume el modelo cumplen lo publicado en el
contrato: columnas, claves, rangos y, sobre todo, que NO haya fuga de datos
(los objetivos futuros deben salir de la semana correcta). Si algo falla,
termina con codigo 1 y lista cada problema.

Pensado para tres usos:
  - ultimo paso de scripts/pipeline_completo.py;
  - prueba de humo de quien entrene el modelo (Fase 2) antes de empezar;
  - prueba de quien escriba tests (Dilan): un cambio de columna rompe aqui.

Uso:
    python scripts/validar_contrato.py
"""

import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE_DIR, "data", "processed")

COLUMNAS_PANEL_DENGUE = [
    "departamento", "municipio", "anio", "semana_epidemiologica", "casos_dengue",
    "temperatura_media", "humedad_media", "precipitacion_total_mm",
    "temperatura_media_lag1", "temperatura_media_lag4", "temperatura_media_media_movil_4sem",
    "humedad_media_lag1", "humedad_media_lag4", "humedad_media_media_movil_4sem",
    "precipitacion_total_mm_lag1", "precipitacion_total_mm_lag4",
    "precipitacion_total_mm_media_movil_4sem",
    "fuente_clima", "tiene_clima",
    "senamhi_temperatura_media", "senamhi_humedad_media", "senamhi_precipitacion_total_mm",
    "casos_dengue_lag1", "casos_dengue_lag2", "casos_dengue_lag3", "casos_dengue_lag4",
    "casos_dengue_acum_4sem", "casos_dengue_t_mas_3", "casos_dengue_t_mas_4",
    "hay_casos_t_mas_3",
]
COLUMNAS_PANEL_MALARIA = [
    "municipio", "anio", "se_inicio", "se_fin", "n_semanas", "tipo_bloque",
    "casos_vivax", "casos_falciparum", "casos_mixta", "casos_total", "casos_por_semana",
    "revision_negativa", "fila_inconsistente", "primer_acumulado",
    "temperatura_media_bloque", "temperatura_media_previas4",
    "humedad_media_bloque", "humedad_media_previas4",
    "precipitacion_semanal_mm_bloque", "precipitacion_semanal_mm_previas4", "fuente_clima",
]

errores: list[str] = []


def check(cond: bool, mensaje: str):
    if not cond:
        errores.append(mensaje)


def leer(nombre: str) -> pd.DataFrame | None:
    ruta = os.path.join(PROC, nombre)
    if not os.path.exists(ruta):
        errores.append(f"{nombre}: no existe")
        return None
    return pd.read_csv(ruta)


def validar_dengue():
    p = leer("panel_semanal_dengue_clima.csv")
    if p is None:
        return
    faltan = [c for c in COLUMNAS_PANEL_DENGUE if c not in p.columns]
    check(not faltan, f"panel dengue: faltan columnas {faltan}")
    if faltan:
        return
    clave = ["municipio", "anio", "semana_epidemiologica"]
    check(not p.duplicated(clave).any(), "panel dengue: hay claves municipio-semana repetidas")
    check(p["semana_epidemiologica"].between(1, 13).all(), "panel dengue: semanas fuera de 1-13")
    check((p["casos_dengue"] >= 0).all() and p["casos_dengue"].notna().all(),
          "panel dengue: casos_dengue negativo o vacio")
    for c in ["temperatura_media", "humedad_media", "precipitacion_total_mm",
              "temperatura_media_lag4", "precipitacion_total_mm_media_movil_4sem"]:
        check(p[c].notna().all(), f"panel dengue: {c} tiene NaN (el contrato dice que no)")
    check(p["tiene_clima"].all(), "panel dengue: hay filas con tiene_clima = False")
    check(p["humedad_media"].between(0, 100).all(), "panel dengue: humedad fuera de 0-100")
    check(p["precipitacion_total_mm"].ge(0).all(), "panel dengue: precipitacion negativa")

    # Cada municipio con las 13 semanas completas
    cuenta = p.groupby("municipio")["semana_epidemiologica"].nunique()
    check((cuenta == 13).all(), f"panel dengue: municipios sin las 13 semanas: {list(cuenta[cuenta != 13].index)}")

    # ANTI-FUGA: el objetivo t+h es el casos_dengue de la semana +h del mismo municipio
    # y los rezagos son de semanas ANTERIORES.
    idx = p.set_index(["municipio", "semana_epidemiologica"])["casos_dengue"]
    for h, col in ((3, "casos_dengue_t_mas_3"), (4, "casos_dengue_t_mas_4")):
        esperado = [idx.get((m, s + h)) for m, s in zip(p["municipio"], p["semana_epidemiologica"])]
        esperado = pd.Series(esperado, index=p.index, dtype="float64")
        check(esperado.fillna(-1).eq(p[col].fillna(-1)).all(), f"panel dengue: {col} NO coincide con casos de la semana +{h} (posible fuga)")
    for k in (1, 2, 3, 4):
        esperado = pd.Series([idx.get((m, s - k)) for m, s in zip(p["municipio"], p["semana_epidemiologica"])],
                             index=p.index, dtype="float64")
        check(esperado.fillna(-1).eq(p[f"casos_dengue_lag{k}"].fillna(-1)).all(),
              f"panel dengue: casos_dengue_lag{k} NO coincide con la semana -{k} (posible fuga)")
    check(p.loc[p["semana_epidemiologica"] > 10, "casos_dengue_t_mas_3"].isna().all(),
          "panel dengue: hay objetivo t+3 mas alla de SE13 (inventado)")

    # Cruce con otro archivo: la suma semanal debe igualar el acumulado validado.
    val = leer("dengue_municipal_validado.csv")
    if val is not None:
        acum = val.set_index("municipio")["casos_dengue_acumulados_se1_13"]
        suma = p.groupby("municipio")["casos_dengue"].sum()
        dif = [m for m in suma.index if m in acum.index and suma[m] != acum[m]]
        check(not dif, f"panel dengue: suma semanal != acumulado validado en {dif}")


def validar_malaria():
    p = leer("panel_bloques_malaria_clima.csv")
    if p is None:
        return
    faltan = [c for c in COLUMNAS_PANEL_MALARIA if c not in p.columns]
    check(not faltan, f"panel malaria: faltan columnas {faltan}")
    if faltan:
        return
    check((p["n_semanas"] == p["se_fin"] - p["se_inicio"] + 1).all(),
          "panel malaria: n_semanas inconsistente con se_inicio/se_fin")
    for mun, g in p.sort_values("se_inicio").groupby("municipio"):
        check(g["se_inicio"].iloc[0] == 1, f"panel malaria: {mun} no empieza en SE1")
        contiguos = (g["se_inicio"].values[1:] == g["se_fin"].values[:-1] + 1).all()
        check(bool(contiguos), f"panel malaria: {mun} tiene bloques con huecos o solapados")
    util = p["casos_total"].notna()
    check(((p.loc[util, "casos_total"] / p.loc[util, "n_semanas"]) - p.loc[util, "casos_por_semana"]).abs().max() < 1e-9,
          "panel malaria: casos_por_semana != casos_total / n_semanas")
    check((p.loc[util, ["casos_vivax", "casos_falciparum", "casos_mixta", "casos_total"]] >= 0).all().all(),
          "panel malaria: casos negativos presentes como utilizables")
    check(((p.loc[util, ["casos_vivax", "casos_falciparum", "casos_mixta"]].sum(axis=1)) == p.loc[util, "casos_total"]).all(),
          "panel malaria: vivax+falciparum+mixta != total en bloques utilizables")
    # El ultimo corte debe reproducir el acumulado SE1-13 validado.
    val = leer("malaria_municipal_validado.csv")
    if val is not None:
        suma = p[p["casos_total"].notna()].groupby("municipio")["casos_total"].sum()
        acum = val.set_index("municipio")["total_malaria"]
        dif = [m for m in acum.index if m in suma.index and suma[m] != acum[m]
               and not p[(p.municipio == m)]["casos_total"].isna().any()]
        check(not dif, f"panel malaria: suma de bloques != acumulado SE1-13 validado en {dif}")


def main():
    print("=" * 60)
    print("VALIDACION DEL CONTRATO DE DATOS")
    print("=" * 60)
    validar_dengue()
    validar_malaria()
    if errores:
        print(f"\n{len(errores)} PROBLEMA(S):")
        for e in errores:
            print(f"  - {e}")
        return 1
    print("\nOK: los paneles cumplen el contrato (columnas, claves, rangos y anti-fuga).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
