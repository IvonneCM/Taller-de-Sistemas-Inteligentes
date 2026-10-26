"""
Ubicacion y LIMITES de los municipios con epidemiologia real (version 2)
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (2026-10-26)

Por que existe: `scripts/geocodificar_municipios.py` (version 1) valida el
resultado solo comprobando que el nombre del departamento aparezca en el texto
devuelto, y eso deja pasar errores: ALTO BENI quedo en una calle de La Paz
(a ~130 km del municipio) y SANTA ROSA (BNI) en un caserio homonimo (~110 km).
Ademas la tabla `municipios` exige un poligono (`geometria` MULTIPOLYGON NOT
NULL) y la version 1 solo guarda puntos.

Esta version 2 NO reemplaza ni modifica los archivos de la version 1 (los usa
`dvc.yaml`); escribe archivos NUEVOS:
    data/reference/municipios_ubicacion.csv   ubicacion corregida + procedencia
    data/reference/municipios_limites.geojson limites administrativos (poligonos)

Fuente: OpenStreetMap / Nominatim (licencia ODbL).

Reglas para no inventar datos:
  - Se prefiere el LIMITE ADMINISTRATIVO (relacion `boundary/administrative` de
    nivel municipio, place_rank 14-18) cuyo primer componente contiene el nombre
    del municipio; su poligono se guarda tal cual lo entrega OSM.
  - Si OSM solo tiene un punto (localidad), la fila queda con
    `tipo_resultado = punto` y NO se fabrica un poligono (quien lo necesite usa
    un cuadrado referencial explicito, como la zona piloto).
  - No basta con que el departamento aparezca en el texto: el nombre debe estar
    en el primer componente. Si no se cumple, `revisar_manual = True`.
  - Cada fila guarda la consulta, el `display_name` y el identificador OSM para
    auditar a mano.

Correcciones conocidas (CONSULTAS_ESPECIALES): ALTO BENI, SANTA ROSA (BNI),
BUENA VISTA (OSM devolvia otro "Buena Vista", a ~590 km) y CERCADO TJ.

Es de UNA SOLA EJECUCION (~2 min: Nominatim permite 1 consulta por segundo).
Si el CSV existe, solo se consultan municipios nuevos; `--rehacer` repite todo.

Uso:
    python scripts/geocodificar_limites.py
    python scripts/geocodificar_limites.py --rehacer
"""

import json
import os
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENGUE_FILE = os.path.join(BASE_DIR, "data", "processed", "dengue_municipal_validado.csv")
MALARIA_FILE = os.path.join(BASE_DIR, "data", "processed", "malaria_municipal_validado.csv")
UBICACION_FILE = os.path.join(BASE_DIR, "data", "reference", "municipios_ubicacion.csv")
LIMITES_FILE = os.path.join(BASE_DIR, "data", "reference", "municipios_limites.geojson")

USER_AGENT = "TallerSistemasInteligentes-proyecto-academico/1.0 (dengue-malaria Bolivia)"
BBOX_BOLIVIA = (-23.0, -9.0, -70.0, -57.0)  # lat_min, lat_max, lon_min, lon_max

# Nombre del boletin -> (consulta a Nominatim, departamento esperado).
CONSULTAS_ESPECIALES = {
    "ALTO BENI": ("Municipio Alto Beni, Provincia Caranavi, La Paz, Bolivia", "LA PAZ"),
    "SANTA ROSA (BNI)": ("Santa Rosa de Yacuma, Beni, Bolivia", "BENI"),
    "BUENA VISTA": ("Municipio Buena Vista, Provincia Ichilo, Santa Cruz, Bolivia", "SANTA CRUZ"),
    "CERCADO TJ": ("Municipio Tarija, Provincia Cercado, Tarija, Bolivia", "TARIJA"),
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

# Nombre con el que OSM conoce al municipio cuando difiere del boletin.
ALIAS_NOMBRE = {"CERCADO TJ": ["TARIJA"]}

# Departamento de los municipios que solo aparecen en malaria.
DEPARTAMENTO_FALLBACK = {
    "RURRENABAQUE": "BENI", "SAN BUENAVENTURA": "LA PAZ", "IXIAMAS": "LA PAZ", "COBIJA": "PANDO",
}


def universo_municipios() -> pd.DataFrame:
    d = pd.read_csv(DENGUE_FILE)[["municipio", "departamento"]]
    m = pd.read_csv(MALARIA_FILE)[["municipio"]]
    base = d.drop_duplicates("municipio")
    extra = m[~m["municipio"].isin(base["municipio"])].drop_duplicates()
    extra = extra.assign(departamento=extra["municipio"].map(DEPARTAMENTO_FALLBACK))
    return pd.concat([base, extra], ignore_index=True)


def consultar(query: str) -> list[dict]:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 5, "countrycodes": "bo", "polygon_geojson": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return "".join(ch for ch in s if ch.isalnum())


def elegir(resultados: list[dict], municipio: str, dep: str) -> tuple[dict | None, str]:
    """(resultado, tipo): tipo = 'limite_administrativo' | 'punto' | 'punto_dudoso' | ''."""
    dep_ok = [r for r in resultados if not dep or _norm(dep) in _norm(r["display_name"])]
    nombres = {_norm(p) for p in municipio.replace(")", "").split("(") if p.strip()}
    nombres |= {_norm(a) for a in ALIAS_NOMBRE.get(municipio, [])}

    def nombre_en_primer_componente(r):
        primero = _norm(r["display_name"].split(",")[0])
        return any(n and (n in primero or primero in n) for n in nombres)

    for r in dep_ok:
        g = r.get("geojson") or {}
        if (r.get("class") == "boundary" and r.get("type") == "administrative"
                and 14 <= int(r.get("place_rank", 0)) <= 18
                and g.get("type") in ("Polygon", "MultiPolygon")
                and nombre_en_primer_componente(r)):
            return r, "limite_administrativo"
    for r in dep_ok:
        if r.get("class") in ("place", "boundary", "landuse", "aeroway") and nombre_en_primer_componente(r):
            return r, "punto"
    return (dep_ok[0], "punto_dudoso") if dep_ok else (None, "")


def main():
    rehacer = "--rehacer" in sys.argv
    universo = universo_municipios()
    previo = pd.read_csv(UBICACION_FILE) if (os.path.exists(UBICACION_FILE) and not rehacer) else pd.DataFrame()
    ya = set(previo["municipio"]) if len(previo) else set()
    filas = previo.to_dict("records") if len(previo) else []
    limites = {}
    if os.path.exists(LIMITES_FILE) and not rehacer:
        with open(LIMITES_FILE, encoding="utf-8") as f:
            limites = {ft["properties"]["municipio"]: ft for ft in json.load(f)["features"]}

    for _, f in universo.iterrows():
        mun = f["municipio"]
        if mun in ya:
            continue
        if mun in CONSULTAS_ESPECIALES:
            query, dep = CONSULTAS_ESPECIALES[mun]
        else:
            dep = f["departamento"] if isinstance(f["departamento"], str) else ""
            query = f"{mun.title()}, {dep.title()}, Bolivia" if dep else f"{mun.title()}, Bolivia"
        consultas = [query] + ([f"Municipio {query}"] if "Municipio" not in query else [])
        elegido, tipo = None, ""
        for q in consultas:
            try:
                res = consultar(q)
            except Exception as e:  # red caida, limite de uso, etc.
                print(f"  ERROR {mun}: {e}")
                res = []
            time.sleep(1.1)  # politica de uso de Nominatim: max 1 consulta/segundo
            cand, tip = elegir(res, mun, dep)
            if cand is not None and (elegido is None or tip == "limite_administrativo"):
                elegido, tipo, query = cand, tip, q
            if tipo == "limite_administrativo":
                break

        lat = lon = None
        nombre = osm = clase = ""
        if elegido:
            lat, lon, nombre = float(elegido["lat"]), float(elegido["lon"]), elegido["display_name"]
            osm = f"{elegido['osm_type']}/{elegido['osm_id']}"
            clase = f"{elegido.get('class')}/{elegido.get('type')}"
            if not (BBOX_BOLIVIA[0] <= lat <= BBOX_BOLIVIA[1] and BBOX_BOLIVIA[2] <= lon <= BBOX_BOLIVIA[3]):
                lat = lon = None
            if tipo == "limite_administrativo" and lat is not None:
                limites[mun] = {
                    "type": "Feature",
                    "properties": {"municipio": mun, "osm": osm, "fuente": "OpenStreetMap (ODbL)",
                                   "tipo": "limite_administrativo"},
                    "geometry": elegido["geojson"],
                }
        revisar = (lat is None) or tipo in ("punto_dudoso", "")
        filas.append({
            "municipio": mun, "departamento_esperado": dep, "latitud": lat, "longitud": lon,
            "tipo_resultado": tipo or "sin_resultado", "osm": osm, "clase_osm": clase,
            "consulta": query, "display_name": nombre, "revisar_manual": revisar,
            "fuente": "OpenStreetMap/Nominatim (ODbL)",
        })
        print(f"  {mun:30s} {tipo or 'SIN RESULTADO':22s} ({lat}, {lon}) {'REVISAR' if revisar else ''}")

    os.makedirs(os.path.dirname(UBICACION_FILE), exist_ok=True)
    pd.DataFrame(filas).to_csv(UBICACION_FILE, index=False, encoding="utf-8-sig")
    with open(LIMITES_FILE, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": list(limites.values())}, f, ensure_ascii=False)
    n_lim = sum(1 for r in filas if r.get("tipo_resultado") == "limite_administrativo")
    print(f"\nGuardado: {UBICACION_FILE} ({len(filas)} municipios, {n_lim} con limite administrativo)")
    print(f"          {LIMITES_FILE}")


if __name__ == "__main__":
    main()
