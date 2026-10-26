"""
Panel semanal municipio-semana: dengue real + clima, con rezagos y objetivos
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25, version 2)

Una fila por combinacion municipio-semana, con los casos de dengue de ESA
semana (Boletin Epidemiologico N.13, ver scripts/extraer_dengue_semanal.py)
y el clima de ESA semana.

CAMBIOS RESPECTO A LA VERSION 1 (el contrato se actualiza en el mismo commit):
  - Cobertura: de 4 municipios (con SENAMHI) a TODOS los municipios con
    dengue reportado (28). Clima uniforme de NASA POWER
    (scripts/clima_nasa_power.py).
  - SENAMHI se conserva como columnas `senamhi_*` (solo 4 municipios) para
    comparar; NO se mezcla con NASA en las mismas columnas.
  - Rezagos y medias moviles del clima se calculan sobre la serie completa
    (desde oct-2025), por lo que ya no hay NaN artificiales en SE1-SE4.
  - Se agregan rezagos de casos y los objetivos a 3 y 4 semanas, que es el
    horizonte del producto (alerta temprana con 3-4 semanas de anticipacion).

Lo que NO hace (a proposito):
  - No define "brote". Esa es la variable objetivo del modelo (Fase 2): con
    13 semanas no hay historia para un umbral epidemiologico defendible.
    Se entregan los conteos futuros y una marca neutra `hay_casos_t_mas_3`.
  - No agrega poblacion: la unica que se podria derivar de los boletines
    (casos / incidencia) viene redondeada y tiene errores de hasta +-50 %.
  - Un municipio que no aparece en la tabla de dengue NO se rellena con
    ceros: se desconoce si no tuvo casos o no reporto.

Entrada:
    data/processed/dengue_municipal_semanal.csv
    data/processed/clima_nasa_power_semanal.csv
    data/processed/clima_semanal.csv  (SENAMHI, opcional)
Salida:
    data/processed/panel_semanal_dengue_clima.csv
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE_DIR, "data", "processed")
DENGUE_FILE = os.path.join(PROC, "dengue_municipal_semanal.csv")
NASA_FILE = os.path.join(PROC, "clima_nasa_power_semanal.csv")
SENAMHI_FILE = os.path.join(PROC, "clima_semanal.csv")
OUTPUT_FILE = os.path.join(PROC, "panel_semanal_dengue_clima.csv")

VARIABLES_CLIMA = ["temperatura_media", "humedad_media", "precipitacion_total_mm"]
LAGS = [1, 2, 3, 4]
VENTANAS = [2, 3, 4]
HORIZONTES = [3, 4]


def clima_con_ventanas(nasa: pd.DataFrame) -> pd.DataFrame:
    """Rezagos y medias moviles sobre la serie completa de cada municipio."""
    nasa = nasa.sort_values(["municipio", "anio", "semana_epidemiologica"]).copy()
    g = nasa.groupby("municipio")
    for v in VARIABLES_CLIMA:
        for k in LAGS:
            nasa[f"{v}_lag{k}"] = g[v].shift(k)
        for w in VENTANAS:
            nasa[f"{v}_media_movil_{w}sem"] = g[v].transform(
                lambda s, w=w: s.rolling(w, min_periods=w).mean()
            )
    return nasa


def main():
    print("=" * 60)
    print("PANEL SEMANAL v2: dengue real + clima NASA POWER (+ SENAMHI)")
    print("=" * 60)

    dengue = pd.read_csv(DENGUE_FILE)
    nasa = clima_con_ventanas(pd.read_csv(NASA_FILE))

    cols_clima = (
        ["municipio", "anio", "semana_epidemiologica"]
        + VARIABLES_CLIMA
        + [c for c in nasa.columns if "_lag" in c or "media_movil" in c]
    )
    panel = dengue.merge(
        nasa[cols_clima], on=["municipio", "anio", "semana_epidemiologica"], how="left"
    )
    panel["fuente_clima"] = panel["temperatura_media"].notna().map(
        {True: "NASA POWER (reanalisis)", False: None}
    )
    panel["tiene_clima"] = panel["temperatura_media"].notna()

    # SENAMHI: columnas aparte, solo donde existe.
    if os.path.exists(SENAMHI_FILE):
        sen = pd.read_csv(SENAMHI_FILE)[
            ["municipio", "anio", "semana_epidemiologica",
             "temperatura_media", "humedad_media", "precipitacion_total_mm",
             "cobertura_suficiente"]
        ].rename(columns={
            "temperatura_media": "senamhi_temperatura_media",
            "humedad_media": "senamhi_humedad_media",
            "precipitacion_total_mm": "senamhi_precipitacion_total_mm",
            "cobertura_suficiente": "senamhi_cobertura_suficiente",
        })
        panel = panel.merge(sen, on=["municipio", "anio", "semana_epidemiologica"], how="left")

    # Rezagos de casos y objetivos futuros, dentro de cada municipio.
    panel = panel.sort_values(["municipio", "anio", "semana_epidemiologica"]).reset_index(drop=True)
    g = panel.groupby("municipio")["casos_dengue"]
    for k in LAGS:
        panel[f"casos_dengue_lag{k}"] = g.shift(k)
    panel["casos_dengue_acum_4sem"] = g.transform(lambda s: s.rolling(4, min_periods=4).sum())
    for h in HORIZONTES:
        panel[f"casos_dengue_t_mas_{h}"] = g.shift(-h)
    panel["hay_casos_t_mas_3"] = panel["casos_dengue_t_mas_3"].gt(0).where(
        panel["casos_dengue_t_mas_3"].notna()
    )

    # Un panel con 0 filas utiles seria un error silencioso: se detiene.
    if panel.empty or not panel["tiene_clima"].any():
        raise SystemExit("ERROR: el panel quedo vacio o sin clima; no se guarda.")

    panel.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    util = panel["casos_dengue_t_mas_3"].notna() & panel["casos_dengue_lag1"].notna()
    print(f"\nFilas del panel: {len(panel)}  |  municipios: {panel['municipio'].nunique()}")
    print(f"Filas con clima: {int(panel['tiene_clima'].sum())}")
    print(f"Filas con SENAMHI: {int(panel.get('senamhi_temperatura_media', pd.Series(dtype=float)).notna().sum())}")
    print(f"Filas utilizables para predecir t+3 (con lag1 y objetivo): {int(util.sum())}")
    print(f"Filas con objetivo t+3 con casos > 0: {int((panel['casos_dengue_t_mas_3'] > 0).sum())}")
    print(f"\nGuardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
