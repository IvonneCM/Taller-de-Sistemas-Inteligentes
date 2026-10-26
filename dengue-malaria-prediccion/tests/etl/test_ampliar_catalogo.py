"""Verificacion de app/etl/ampliar_catalogo.py: ampliacion OPCIONAL del catalogo.

La ampliacion no debe filtrarse al catalogo base: `seed_catalogo` sigue
cargando solo los 4 municipios piloto y estos tests lo comprueban."""

import json

import pandas as pd
import pytest
from sqlalchemy import text

from app.etl.ampliar_catalogo import (
    LIMITES_GEOJSON,
    UBICACION_CSV,
    ampliar_catalogo,
    geojson_a_wkt_multipoligono,
)
from app.models import Municipio

PILOTO = {"GUAYARAMERIN", "IXIAMAS", "PALOS BLANCOS", "SAN BUENAVENTURA"}
HAY_REFERENCIAS = UBICACION_CSV.exists() and LIMITES_GEOJSON.exists()


def test_geojson_polygon_se_convierte_en_multipolygon_con_huecos():
    poligono = {"type": "Polygon", "coordinates": [
        [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
        [[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]],  # hueco
    ]}
    assert geojson_a_wkt_multipoligono(poligono) == (
        "MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0),(1 1, 2 1, 2 2, 1 2, 1 1)))"
    )


def test_geojson_multipolygon_conserva_todos_los_poligonos():
    multi = {"type": "MultiPolygon", "coordinates": [
        [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        [[[5, 5], [6, 5], [6, 6], [5, 5]]],
    ]}
    wkt = geojson_a_wkt_multipoligono(multi)
    assert wkt.startswith("MULTIPOLYGON(((") and wkt.count("((") == 2


def test_geojson_de_punto_no_se_acepta_como_municipio():
    with pytest.raises(ValueError, match="no soportada"):
        geojson_a_wkt_multipoligono({"type": "Point", "coordinates": [0, 0]})


def test_el_seed_base_sigue_siendo_solo_la_zona_piloto(db_session):
    nombres = {m.nombre for m in db_session.query(Municipio).all()}
    assert nombres == PILOTO  # la ampliacion es opt-in: no se ejecuta sola


def test_no_se_inventa_ubicacion_si_falta_el_poligono_y_el_punto(db_session, tmp_path):
    csv = tmp_path / "ubicacion.csv"
    pd.DataFrame([{"municipio": "MUNICIPIO_SIN_UBICACION", "departamento_esperado": "BENI",
                   "latitud": None, "longitud": None}]).to_csv(csv, index=False)
    geo = tmp_path / "limites.geojson"
    geo.write_text(json.dumps({"type": "FeatureCollection", "features": []}))

    resumen = ampliar_catalogo(db_session, ubicacion=csv, limites=geo)

    assert resumen["creados"] == 0
    assert resumen["sin_ubicacion"] == ["MUNICIPIO_SIN_UBICACION"]


def test_faltan_los_archivos_de_referencia_da_un_mensaje_claro(db_session, tmp_path):
    with pytest.raises(FileNotFoundError, match="geocodificar_limites"):
        ampliar_catalogo(db_session, ubicacion=tmp_path / "no.csv", limites=tmp_path / "no.geojson")


@pytest.mark.skipif(not HAY_REFERENCIAS, reason="data/reference sin generar (scripts/geocodificar_limites.py)")
def test_ampliacion_real_agrega_municipios_validos_sin_tocar_el_piloto(db_session):
    antes = dict(db_session.execute(
        text("SELECT nombre, ST_AsText(geometria) FROM municipios")).all())

    resumen = ampliar_catalogo(db_session)

    assert resumen["creados"] == 38 and resumen["total_municipios"] == 42
    assert resumen["con_limite_osm"] == 37
    assert resumen["con_cuadrado_referencial"] == ["SANTA ROSA (BNI)"]
    # Geometrias de PostGIS: validas, MultiPolygon y SRID 4326.
    malas = db_session.execute(text(
        "SELECT count(*) FROM municipios WHERE NOT ST_IsValid(geometria) "
        "OR ST_SRID(geometria) <> 4326 OR GeometryType(geometria) <> 'MULTIPOLYGON'")).scalar()
    assert malas == 0
    # El piloto conserva exactamente su geometria referencial.
    despues = dict(db_session.execute(
        text("SELECT nombre, ST_AsText(geometria) FROM municipios WHERE nombre = ANY(:n)"),
        {"n": list(PILOTO)}).all())
    assert despues == antes
    # Nombres unicos: los conectores buscan por nombre.
    repetidos = db_session.execute(text(
        "SELECT count(*) FROM (SELECT nombre FROM municipios GROUP BY nombre HAVING count(*) > 1) x")).scalar()
    assert repetidos == 0


@pytest.mark.skipif(not HAY_REFERENCIAS, reason="data/reference sin generar (scripts/geocodificar_limites.py)")
def test_ampliacion_es_idempotente(db_session):
    ampliar_catalogo(db_session)
    segunda = ampliar_catalogo(db_session)
    assert segunda["creados"] == 0 and segunda["total_municipios"] == 42
