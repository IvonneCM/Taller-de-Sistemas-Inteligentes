"""
Inventario de estaciones SENAMHI (no descarga clima, solo identifica
qué estaciones estan reportando y donde).

Correr desde una maquina con internet (NO funciona desde el entorno de
Claude en la nube, el proxy lo bloquea):

    python inventario_estaciones_senamhi.py

Genera: estaciones_senamhi_detectadas.csv
Columnas: wigos_id, latitud, longitud, primera_fecha_vista, veces_vista
"""

import requests
import pandas as pd

URL = (
    "https://wis.senamhi.gob.bo/oapi/collections/"
    "urn%3Awmo%3Amd%3Abo-senamhi%3A51lca7/items"
)

estaciones = {}  # wigos_id -> {lat, lon, veces, primera_fecha}

offset = 0
limit = 1000
pagina = 1

print("Escaneando estaciones reportando en la coleccion nacional...\n")

while True:
    print(f"Pagina {pagina} (offset {offset})...")
    r = requests.get(URL, params={"f": "json", "limit": limit, "offset": offset}, timeout=(15, 120))
    r.raise_for_status()
    datos = r.json()
    features = datos.get("features", [])

    if not features:
        print("No hay mas registros.")
        break

    for feature in features:
        props = feature.get("properties", {}) or {}
        wigos = props.get("wigos_station_identifier")
        if not wigos:
            continue

        geom = feature.get("geometry") or {}
        coords = geom.get("coordinates") or []
        lon = coords[0] if len(coords) >= 1 else None
        lat = coords[1] if len(coords) >= 2 else None
        fecha = props.get("reportTime")

        if wigos not in estaciones:
            estaciones[wigos] = {"latitud": lat, "longitud": lon, "veces_vista": 0, "primera_fecha_vista": fecha}
        estaciones[wigos]["veces_vista"] += 1

    links = datos.get("links", [])
    existe_next = any(link.get("rel") == "next" for link in links)
    if not existe_next:
        print("Fin de paginas.")
        break

    offset += limit
    pagina += 1

    # Limite de seguridad: si ya vimos muchas paginas y las estaciones
    # dejaron de cambiar, no hace falta recorrer todo el historico.
    if pagina > 60:
        print("Corte de seguridad en 60 paginas (suficiente para detectar estaciones).")
        break

df = pd.DataFrame([
    {"wigos_id": k, **v} for k, v in estaciones.items()
]).sort_values("veces_vista", ascending=False)

df.to_csv("estaciones_senamhi_detectadas.csv", index=False, encoding="utf-8-sig")

print(f"\nTotal de estaciones distintas detectadas: {len(df)}")
print(df.to_string(index=False))
print("\nGuardado en: estaciones_senamhi_detectadas.csv")
