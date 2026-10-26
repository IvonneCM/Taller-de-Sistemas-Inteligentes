"""
Coordenadas de los municipios con epidemiologia real
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Por que existe: SENAMHI solo cubre 4 municipios; para darle clima a todos
los municipios con casos reportados (reanalisis NASA POWER) hace falta un
punto (lat, lon) por municipio. Ningun boletin trae coordenadas.

Fuente: OpenStreetMap / Nominatim (https://nominatim.openstreetmap.org),
licencia ODbL. Se toma el punto representativo que devuelve Nominatim
para el municipio (centro del limite administrativo cuando existe).

Reglas para no inventar datos:
  - Cada fila guarda la consulta hecha y el `display_name` devuelto, para
    poder auditar a mano que el resultado sea el municipio correcto.
  - Un resultado fuera de Bolivia se rechaza (queda sin coordenada).
  - Se marca `revisar_manual = True` cuando el departamento esperado no
    aparece en el `display_name`.
  - Es un script de UNA SOLA EJECUCION: el resultado se versiona en
    data/reference/municipios_coordenadas.csv y el pipeline lee ese
    archivo. Si el archivo existe, solo se consultan municipios nuevos.

Uso:
    python scripts/geocodificar_municipios.py
"""

import json
import os
import time
import urllib.parse
import urllib.request

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENGUE_FILE = os.path.join(BASE_DIR, "data", "processed", "dengue_municipal_validado.csv")
MALARIA_FILE = os.path.join(BASE_DIR, "data", "processed", "malaria_municipal_validado.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "reference", "municipios_coordenadas.csv")

USER_AGENT = "TallerSistemasInteligentes-proyecto-academico/1.0 (dengue-malaria Bolivia)"
BBOX_BOLIVIA = (-23.0, -9.0, -70.0, -57.0)  # lat_min, lat_max, lon_min, lon_max

# Nombre del boletin -> (consulta a Nominatim, departamento esperado).
# Solo se listan los que NO se pueden consultar tal cual; el resto usa
# "<nombre>, <departamento>, Bolivia".
CONSULTAS_ESPECIALES = {
    "CERCADO TJ": ("Tarija, Cercado, Bolivia", "TARIJA"),
    "SANTA ROSA (BNI)": ("Santa Rosa del Yacuma, Beni, Bolivia", "BENI"),
    "SAN LORENZO(PND)": ("San Lorenzo, Pando, Bolivia", "PANDO"),
    "SAN PEDRO(PND)": ("San Pedro, Pando, Bolivia", "PANDO"),
    "INGAVI(HUMAITA)": ("Humaita, Pando, Bolivia", "PANDO"),
    "EUREKA(SANTOS MERCADO)": ("Santos Mercado, Pando, Bolivia", "PANDO"),
    "NACEBE(SANTA ROSA DEL ABUNA)": ("Santa Rosa del Abuna, Pando, Bolivia", "PANDO"),
    "NUEVO MANOA(NUEVA ESPERANZA)": ("Nueva Esperanza, Pando, Bolivia", "PANDO"),
    "VILLA NUEVA (LOMA ALTA)": ("Loma Alta, Pando, Bolivia", "PANDO"),
    "PUERTO GONZALO MORENO": ("Puerto Gonzalo Moreno, Pando, Bolivia", "PANDO"),
    "SENA": ("Sena, Pando, Bolivia", "PANDO"),
    "PORVENIR": ("Porvenir, Pando, Bolivia", "PANDO"),
    "PUERTO RICO": ("Puerto Rico, Pando, Bolivia", "PANDO"),
    "BELLA FLOR": ("Bella Flor, Pando, Bolivia", "PANDO"),
    "REYES": ("Reyes, Beni, Bolivia", "BENI"),
    "PUERTO QUIJARRO": ("Puerto Quijarro, Santa Cruz, Bolivia", "SANTA CRUZ"),
    "CAMIRI": ("Camiri, Santa Cruz, Bolivia", "SANTA CRUZ"),
}

# Departamento esperado para los municipios que no estan en la tabla de
# dengue (solo aparecen en malaria, donde la columna es "agrupacion SEDES").
DEPARTAMENTO_FALLBACK = {
    "RURRENABAQUE": "BENI",
    "SAN BUENAVENTURA": "LA PAZ",
    "IXIAMAS": "LA PAZ",
    "COBIJA": "PANDO",
}


def universo_municipios() -> pd.DataFrame:
    d = pd.read_csv(DENGUE_FILE)[["municipio", "departamento"]]
    m = pd.read_csv(MALARIA_FILE)[["municipio"]]
    base = d.drop_duplicates("municipio")
    extra = m[~m["municipio"].isin(base["municipio"])].drop_duplicates()
    extra = extra.assign(departamento=extra["municipio"].map(DEPARTAMENTO_FALLBACK))
    return pd.concat([base, extra], ignore_index=True)


def consultar(query: str) -> dict | None:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "bo"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read().decode("utf-8"))
    return res[0] if res else None


def main():
    universo = universo_municipios()
    previo = pd.read_csv(OUTPUT_FILE) if os.path.exists(OUTPUT_FILE) else pd.DataFrame()
    ya = set(previo["municipio"]) if len(previo) else set()

    filas = previo.to_dict("records") if len(previo) else []
    for _, f in universo.iterrows():
        mun = f["municipio"]
        if mun in ya:
            continue
        if mun in CONSULTAS_ESPECIALES:
            query, dep = CONSULTAS_ESPECIALES[mun]
        else:
            dep = f["departamento"] if isinstance(f["departamento"], str) else ""
            query = f"{mun.title()}, {dep.title()}, Bolivia" if dep else f"{mun.title()}, Bolivia"
        try:
            r = consultar(query)
        except Exception as e:  # red caida, limite de uso, etc.
            print(f"  ERROR {mun}: {e}")
            r = None
        time.sleep(1.1)  # politica de uso de Nominatim: max 1 consulta/segundo
        lat = lon = None
        nombre = ""
        if r:
            lat, lon, nombre = float(r["lat"]), float(r["lon"]), r["display_name"]
            if not (BBOX_BOLIVIA[0] <= lat <= BBOX_BOLIVIA[1] and BBOX_BOLIVIA[2] <= lon <= BBOX_BOLIVIA[3]):
                lat = lon = None
        dep_ok = bool(dep) and dep.lower() in nombre.lower()
        filas.append({
            "municipio": mun,
            "departamento_esperado": dep,
            "latitud": lat,
            "longitud": lon,
            "consulta": query,
            "display_name": nombre,
            "revisar_manual": (lat is None) or (not dep_ok),
            "fuente": "OpenStreetMap/Nominatim (ODbL)",
        })
        print(f"  {mun:32s} -> {lat}, {lon}  {'REVISAR' if (lat is None or not dep_ok) else 'ok'}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    pd.DataFrame(filas).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\nGuardado: {OUTPUT_FILE} ({len(filas)} municipios)")


if __name__ == "__main__":
    main()
