"""
Clima de reanalisis (NASA POWER) para TODOS los municipios con casos
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Por que existe: SENAMHI solo cubre 4 de los 28 municipios con dengue
reportado (ver docs/municipios_sin_cobertura_climatica.md). NASA POWER
entrega clima diario modelado para cualquier coordenada, asi que el panel
puede pasar de 4 municipios a todos los que tienen epidemiologia real.

Fuente: NASA POWER (https://power.larc.nasa.gov), comunidad AG, datos
diarios. Variables:
    T2M / T2M_MIN / T2M_MAX  temperatura a 2 m (grados C)
    RH2M                     humedad relativa a 2 m (%)
    PRECTOTCORR              precipitacion corregida (mm/dia)
Resolucion espacial ~0.5 x 0.625 grados: municipios cercanos pueden caer
en la misma celda y compartir valores (es una limitacion real de la
fuente; se documenta en docs/contrato_esquema_datos_procesados.md).

IMPORTANTE -- no es lo mismo que SENAMHI: son datos modelados, no
observados en estacion. Por eso el panel guarda la columna `fuente_clima`
y, para los 4 municipios con ambas fuentes, scripts/comparar_clima.py mide
el sesgo entre las dos.

Semanas: se usa la semana ISO (lunes-domingo), igual que
scripts/procesar_clima.py, para que ambas fuentes sean comparables. Es una
aproximacion a la semana epidemiologica (domingo-sabado), con un desfase de
un dia.

Reproducibilidad: la descarga se hace UNA vez y queda en
data/raw/clima/nasa_power/nasa_power_diario.csv. Si ese archivo existe, no
se consulta la red. Para actualizarlo, borrarlo y volver a correr.

Entrada:  data/reference/municipios_coordenadas.csv
Salida:   data/raw/clima/nasa_power/nasa_power_diario.csv      (crudo)
          data/processed/clima_nasa_power_semanal.csv          (semanal)
"""

import json
import os
import time
import urllib.request

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORD_FILE = os.path.join(BASE_DIR, "data", "reference", "municipios_coordenadas.csv")
RAW_FILE = os.path.join(BASE_DIR, "data", "raw", "clima", "nasa_power", "nasa_power_diario.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "clima_nasa_power_semanal.csv")

# Ventana: desde antes de la ISO-SE1 de 2026 (29-dic-2025) para tener
# historia suficiente para rezagos, hasta fin de la SE13 + margen.
FECHA_INICIO = "20251001"
FECHA_FIN = "20260405"
PARAMETROS = "T2M,T2M_MIN,T2M_MAX,RH2M,PRECTOTCORR"
SENTINELA = -999.0  # valor que NASA POWER usa para "sin dato"


def descargar(solo_faltantes: set | None = None) -> pd.DataFrame:
    coords = pd.read_csv(COORD_FILE).dropna(subset=["latitud", "longitud"])
    if solo_faltantes is not None:
        coords = coords[coords["municipio"].isin(solo_faltantes)]
    filas = []
    for _, c in coords.iterrows():
        url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters={PARAMETROS}&community=AG"
            f"&longitude={c['longitud']}&latitude={c['latitud']}"
            f"&start={FECHA_INICIO}&end={FECHA_FIN}&format=JSON"
        )
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                datos = json.loads(r.read().decode("utf-8"))["properties"]["parameter"]
        except Exception as e:
            print(f"  ERROR {c['municipio']}: {e}")
            continue
        fechas = list(datos["T2M"].keys())
        for f in fechas:
            filas.append({
                "municipio": c["municipio"],
                "fecha": pd.to_datetime(f, format="%Y%m%d"),
                "temperatura_media": datos["T2M"][f],
                "temperatura_min": datos["T2M_MIN"][f],
                "temperatura_max": datos["T2M_MAX"][f],
                "humedad_media": datos["RH2M"][f],
                "precipitacion_24h": datos["PRECTOTCORR"][f],
            })
        print(f"  {c['municipio']:32s} {len(fechas)} dias")
        time.sleep(0.5)
    df = pd.DataFrame(filas)
    if solo_faltantes is not None and os.path.exists(RAW_FILE):
        df = pd.concat([pd.read_csv(RAW_FILE, parse_dates=["fecha"]), df], ignore_index=True)
    os.makedirs(os.path.dirname(RAW_FILE), exist_ok=True)
    df.to_csv(RAW_FILE, index=False, encoding="utf-8-sig")
    return df


def semanal(diario: pd.DataFrame) -> pd.DataFrame:
    d = diario.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    cols = ["temperatura_media", "temperatura_min", "temperatura_max",
            "humedad_media", "precipitacion_24h"]
    # -999 es "sin dato" en NASA POWER: nunca se promedia como valor real.
    d[cols] = d[cols].where(d[cols] != SENTINELA)
    iso = d["fecha"].dt.isocalendar()
    d["anio"] = iso.year.astype(int)
    d["semana_epidemiologica"] = iso.week.astype(int)
    s = d.groupby(["municipio", "anio", "semana_epidemiologica"]).agg(
        temperatura_media=("temperatura_media", "mean"),
        temperatura_min=("temperatura_min", "min"),
        temperatura_max=("temperatura_max", "max"),
        humedad_media=("humedad_media", "mean"),
        precipitacion_total_mm=("precipitacion_24h", "sum"),
        dias_en_semana=("fecha", "count"),
        dias_con_dato=("temperatura_media", "count"),
    ).reset_index()
    s["fuente_clima"] = "NASA POWER (reanalisis)"
    return s


def main():
    print("=" * 60)
    print("CLIMA NASA POWER (reanalisis) por municipio")
    print("=" * 60)
    if os.path.exists(RAW_FILE):
        print(f"Usando crudo ya descargado: {RAW_FILE}")
        diario = pd.read_csv(RAW_FILE)
        coords = pd.read_csv(COORD_FILE).dropna(subset=["latitud", "longitud"])
        faltan = set(coords["municipio"]) - set(diario["municipio"])
        if faltan:
            print(f"Completando municipios que faltaban: {sorted(faltan)}")
            diario = descargar(solo_faltantes=faltan)
    else:
        print("Descargando de NASA POWER (una sola vez)...")
        diario = descargar()
    s = semanal(diario)
    s.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n{len(s)} filas municipio-semana, {s['municipio'].nunique()} municipios")
    print(f"Guardado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
