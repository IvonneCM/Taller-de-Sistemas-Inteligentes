"""
Ampliacion OPCIONAL del catalogo de municipios (mas alla de la zona piloto).

Por que existe: `app/etl/seed_catalogo.py` carga solo los 4 municipios piloto
(decision 1 del reparto). Pero los datos reales cubren 28 municipios con dengue
y 22 con malaria, y los brotes se concentran en municipios que NO estan en el
catalogo (San Borja: 140 casos, Caranavi: 60). Con solo 4 municipios el maximo
semanal es 5 casos y casi no hay brotes que predecir ni validar.

Es OPT-IN: nada lo ejecuta por defecto, `seed_catalogo.seed()` no cambia y los
tests siguen viendo 4 municipios. Se usa asi, ANTES de `seed_demo`:

    python -m app.etl.ampliar_catalogo
    SEED_DEMO_PASSWORD=<clave> python -m app.etl.seed_demo

`seed_demo` ingiere casos solo de municipios del catalogo y omite el resto, asi
que con el catalogo ampliado carga (y predice) todos los municipios.

Geometria (`municipios.geometria` es MULTIPOLYGON NOT NULL):
  - Si existe el limite administrativo de OpenStreetMap
    (data/reference/municipios_limites.geojson, generado por
    scripts/geocodificar_limites.py), se usa ese poligono tal cual.
  - Si solo hay un punto (hoy: SANTA ROSA (BNI)), se usa un cuadrado referencial
    de ~5 km centrado en el punto, igual que los municipios piloto. NO se
    inventa un limite.
  - Los 4 municipios piloto que ya estan en la base NO se modifican (conservan
    su cuadrado referencial centrado en la estacion SENAMHI).
  - Si un poligono de OSM no es valido para PostGIS se repara con ST_MakeValid.

Idempotente: un municipio que ya existe (por nombre) no se vuelve a crear.

Limitacion conocida: `municipios.nombre` no es UNIQUE y los conectores buscan por
nombre; con los 42 municipios actuales no hay nombres repetidos, pero conviene
revisarlo si se agregan mas.

Requiere los archivos de data/reference/ (no se copian a la imagen Docker, que
solo incluye app/): fuera del repo falla con un mensaje claro.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.core.database import SessionLocal
from app.etl import seed_catalogo
from app.models import Departamento, Municipio

# <repo>/data/reference (mismo criterio que seed_demo.PROCESADOS).
REFERENCIA = Path(__file__).resolve().parents[3] / "data" / "reference"
UBICACION_CSV = REFERENCIA / "municipios_ubicacion.csv"
LIMITES_GEOJSON = REFERENCIA / "municipios_limites.geojson"


def _anillo(coords) -> str:
    return "(" + ", ".join(f"{x} {y}" for x, y, *_ in coords) + ")"


def geojson_a_wkt_multipoligono(geometria: dict) -> str:
    """GeoJSON Polygon/MultiPolygon -> WKT MULTIPOLYGON (siempre multi)."""
    tipo = geometria.get("type")
    if tipo == "Polygon":
        poligonos = [geometria["coordinates"]]
    elif tipo == "MultiPolygon":
        poligonos = geometria["coordinates"]
    else:
        raise ValueError(f"Geometria no soportada para municipios: {tipo!r}")
    return "MULTIPOLYGON(" + ",".join(
        "(" + ",".join(_anillo(anillo) for anillo in poligono) + ")" for poligono in poligonos
    ) + ")"


def _cargar_referencias(ubicacion: Path, limites: Path) -> tuple[pd.DataFrame, dict]:
    faltan = [str(p) for p in (ubicacion, limites) if not p.exists()]
    if faltan:
        raise FileNotFoundError(
            f"No se encontraron los archivos de referencia: {faltan}. Generarlos con "
            "`python scripts/geocodificar_limites.py` (requiere red) desde la raiz del repo."
        )
    df = pd.read_csv(ubicacion)
    with open(limites, encoding="utf-8") as f:
        poligonos = {ft["properties"]["municipio"]: ft["geometry"] for ft in json.load(f)["features"]}
    return df, poligonos


def ampliar_catalogo(
    db,
    ubicacion: Path | None = None,
    limites: Path | None = None,
) -> dict:
    """Agrega al catalogo los municipios de data/reference que aun no existen.

    No hace commit: lo hace quien llama (o `main`). Devuelve un resumen."""
    df, poligonos = _cargar_referencias(Path(ubicacion or UBICACION_CSV), Path(limites or LIMITES_GEOJSON))

    departamentos = {d.nombre: d for d in db.query(Departamento).all()}
    existentes = {m.nombre for m in db.query(Municipio).all()}

    creados, con_limite, con_cuadrado, sin_ubicacion = [], [], [], []
    for _, fila in df.iterrows():
        nombre = str(fila["municipio"]).strip().upper()
        if nombre in existentes:
            continue
        dep_nombre = str(fila["departamento_esperado"]).strip().title()
        if not dep_nombre or dep_nombre == "Nan":
            sin_ubicacion.append(nombre)
            continue
        if nombre in poligonos:
            wkt = geojson_a_wkt_multipoligono(poligonos[nombre])
            con_limite.append(nombre)
        elif pd.notna(fila["latitud"]) and pd.notna(fila["longitud"]):
            wkt = seed_catalogo._buffer_wkt(float(fila["latitud"]), float(fila["longitud"]))
            con_cuadrado.append(nombre)
        else:
            sin_ubicacion.append(nombre)  # nunca se inventa una ubicacion
            continue

        if dep_nombre not in departamentos:
            departamentos[dep_nombre] = Departamento(nombre=dep_nombre)
            db.add(departamentos[dep_nombre])
            db.flush()
        m = Municipio(
            nombre=nombre,
            departamento_id=departamentos[dep_nombre].id,
            geometria=f"SRID=4326;{wkt}",
            poblacion_estimada=None,
        )
        db.add(m)
        creados.append(m)
        existentes.add(nombre)
    db.flush()

    reparadas = 0
    if creados:
        ids = [m.id for m in creados]
        reparadas = db.execute(
            text(
                "UPDATE municipios SET geometria = ST_Multi(ST_CollectionExtract(ST_MakeValid(geometria), 3)) "
                "WHERE id = ANY(:ids) AND NOT ST_IsValid(geometria)"
            ),
            {"ids": ids},
        ).rowcount
    return {
        "creados": len(creados),
        "con_limite_osm": len(con_limite),
        "con_cuadrado_referencial": con_cuadrado,
        "sin_ubicacion": sin_ubicacion,
        "geometrias_reparadas": reparadas,
        "total_municipios": db.query(Municipio).count(),
    }


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Amplia el catalogo de municipios (opcional).").parse_args(argv)
    db = SessionLocal()
    try:
        seed_catalogo.seed(db=db)  # asegura departamentos, enfermedades y zona piloto
        resumen = ampliar_catalogo(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Municipios nuevos: {resumen['creados']} "
          f"({resumen['con_limite_osm']} con limite de OpenStreetMap)")
    if resumen["con_cuadrado_referencial"]:
        print(f"Con cuadrado referencial (sin limite en OSM): {resumen['con_cuadrado_referencial']}")
    if resumen["sin_ubicacion"]:
        print(f"Omitidos por falta de ubicacion: {resumen['sin_ubicacion']}")
    if resumen["geometrias_reparadas"]:
        print(f"Geometrias reparadas con ST_MakeValid: {resumen['geometrias_reparadas']}")
    print(f"Total de municipios en el catalogo: {resumen['total_municipios']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
