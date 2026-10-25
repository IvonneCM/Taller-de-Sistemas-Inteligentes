"""
Panel de malaria por bloques de semanas + clima
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Malaria NO tiene serie semanal por municipio en la fuente. Lo que si hay son
bloques reconstruidos por diferencia de acumulados entre boletines
(scripts/extraer_malaria_boletines.py): SE1-5, SE6-7, SE8, SE9, SE10-13.

Este panel une cada bloque con el clima NASA POWER del mismo municipio:
  - `*_bloque`    : clima promedio de las semanas del bloque.
  - `*_previas4`  : clima promedio de las 4 semanas ANTERIORES al bloque
                    (lo que el modelo conoceria antes de que ocurran los
                    casos: es la variable util para predecir).

La unidad de observacion es el BLOQUE, no la semana. Para comparar bloques
de distinto largo se usa `casos_por_semana`. Un bloque de varias semanas
NO se reparte en semanas: seria inventar una granularidad que no existe.

Los bloques sin casos utilizables (fila inconsistente en el boletin o
revision a la baja) se conservan con casos en NaN y NO se usan para entrenar.

Entrada:
    data/processed/malaria_municipal_bloques.csv
    data/processed/clima_nasa_power_semanal.csv
Salida:
    data/processed/panel_bloques_malaria_clima.csv
"""

import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE_DIR, "data", "processed")
BLOQUES_FILE = os.path.join(PROC, "malaria_municipal_bloques.csv")
NASA_FILE = os.path.join(PROC, "clima_nasa_power_semanal.csv")
OUTPUT_FILE = os.path.join(PROC, "panel_bloques_malaria_clima.csv")

VARS = {
    "temperatura_media": "temperatura_media",
    "humedad_media": "humedad_media",
    "precipitacion_total_mm": "precipitacion_semanal_mm",
}


def main():
    print("=" * 60)
    print("PANEL DE MALARIA POR BLOQUES + CLIMA NASA POWER")
    print("=" * 60)
    if not os.path.exists(BLOQUES_FILE):
        print("AVISO: no existe malaria_municipal_bloques.csv; no se genera el panel.")
        return 0 if os.path.exists(OUTPUT_FILE) else 1

    bloques = pd.read_csv(BLOQUES_FILE)
    nasa = pd.read_csv(NASA_FILE)
    # Orden cronologico continuo: ISO-2025 va antes que ISO-2026.
    nasa["t"] = nasa["anio"] * 100 + nasa["semana_epidemiologica"]

    filas = []
    sin_clima = set()
    for _, b in bloques.iterrows():
        n = nasa[nasa["municipio"] == b["municipio"]].sort_values("t")
        if n.empty:
            sin_clima.add(b["municipio"])
        t_ini = 2026 * 100 + int(b["se_inicio"])
        t_fin = 2026 * 100 + int(b["se_fin"])
        en_bloque = n[(n["t"] >= t_ini) & (n["t"] <= t_fin)]
        # 4 semanas inmediatamente anteriores al bloque (cruza de anio).
        previas = n[n["t"] < t_ini].tail(4)
        fila = b.to_dict()
        for v, nombre in VARS.items():
            fila[f"{nombre}_bloque"] = en_bloque[v].mean() if len(en_bloque) else None
            fila[f"{nombre}_previas4"] = previas[v].mean() if len(previas) == 4 else None
        fila["fuente_clima"] = "NASA POWER (reanalisis)"
        filas.append(fila)

    panel = pd.DataFrame(filas)
    if panel.empty:
        raise SystemExit("ERROR: panel de malaria vacio; no se guarda.")
    if sin_clima:
        print(f"AVISO: municipios sin clima NASA: {sorted(sin_clima)}")
    panel.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    utiles = panel["casos_por_semana"].notna()
    print(f"\nBloques: {len(panel)} | municipios: {panel['municipio'].nunique()}")
    print(f"Bloques con casos utilizables: {int(utiles.sum())}")
    print(f"Semanas exactas: {int((panel['n_semanas'] == 1).sum())} | "
          f"bloques de varias semanas: {int((panel['n_semanas'] > 1).sum())}")
    print(f"Guardado: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
