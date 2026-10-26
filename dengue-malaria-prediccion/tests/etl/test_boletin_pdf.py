"""Lectura de boletines en PDF (REQ-014, REQ-013).

Usa los boletines REALES del repo (data/boletines/) y, para los casos de error,
tablas armadas a mano que imitan el formato (no son cifras reales)."""

from pathlib import Path

import pytest

from app.etl.boletin_pdf import (
    BoletinInvalido,
    _interpretar,
    extraer_boletin,
    normalizar_municipio,
)

BOLETINES = Path(__file__).resolve().parents[3] / "data" / "boletines"
requiere_pdf = pytest.mark.skipif(not (BOLETINES / "SE13.pdf").exists(), reason="faltan los boletines en data/boletines")


def _pdf(nombre: str) -> bytes:
    return (BOLETINES / nombre).read_bytes()


@requiere_pdf
def test_boletin_13_coincide_con_el_pipeline():
    e = extraer_boletin(_pdf("SE13.pdf"))
    assert (e.semana, e.anio, e.pagina) == (13, 2026, 8)
    assert len(e.municipios) == 28
    assert e.total == 341  # el mismo total que scripts/extraer_dengue_semanal.py
    guayaramerin = next(f for f in e.municipios if f.clave == "GUAYARAMERIN")
    assert len(guayaramerin.semanas) == 13 and sum(guayaramerin.semanas) == 9


@requiere_pdf
def test_boletin_con_columna_de_departamento():
    e = extraer_boletin(_pdf("SE03.pdf"))  # columnas: Departamento | Municipio | SE1..SE3
    assert e.semana == 3
    assert {"MONTERO", "CARANAVI", "SAN BORJA"} <= {f.clave for f in e.municipios}
    assert e.totales_semana == [17, 13, 5]


@requiere_pdf
def test_boletin_sin_tabla_municipal_se_rechaza_con_motivo():
    with pytest.raises(BoletinInvalido, match="no trae la tabla"):
        extraer_boletin(_pdf("SE21.pdf"))


@requiere_pdf
def test_tabla_partida_entre_paginas_se_rechaza():
    with pytest.raises(BoletinInvalido, match="fila de totales"):
        extraer_boletin(_pdf("SE06.pdf"))


def test_archivo_que_no_es_pdf():
    with pytest.raises(BoletinInvalido, match="no es un PDF"):
        extraer_boletin(b"nombre,casos\nX,1\n")


def test_pdf_corrupto():
    with pytest.raises(BoletinInvalido, match="no se pudo leer"):
        extraer_boletin(b"%PDF-1.4\n esto no es un PDF de verdad")


# --- Tablas armadas a mano (formato del boletin, cifras de ejemplo) ---

def test_tabla_valida_con_total_y_tasa():
    tabla = [
        ["Municipio", "1", "2", "Total", "Tasa"],
        ["San Borja", "3", "", "3", "1,2"],
        ["Riberalta", "1", "2", "3", "0,4"],
        [None, "4", "2", "6", "0,8"],
    ]
    filas, totales = _interpretar(tabla, 2)
    assert [(f.clave, f.semanas) for f in filas] == [("SAN BORJA", [3, 0]), ("RIBERALTA", [1, 2])]
    assert totales == [4, 2]


def test_fila_que_no_suma_su_total_impreso():
    tabla = [["San Borja", "3", "1", "9"], [None, "3", "1", "4"]]
    with pytest.raises(BoletinInvalido, match="San Borja: las semanas suman 4"):
        _interpretar(tabla, 2)


def test_columnas_que_no_suman_la_fila_de_totales():
    tabla = [["San Borja", "3", "1"], ["Total Casos", "5", "1"]]
    with pytest.raises(BoletinInvalido, match="no coincide con la fila de totales"):
        _interpretar(tabla, 2)


def test_municipio_repetido():
    tabla = [["Trinidad", "1"], ["TRINIDAD", "1"], [None, "2"]]
    with pytest.raises(BoletinInvalido, match="repetidos"):
        _interpretar(tabla, 1)


def test_normalizar_municipio():
    assert normalizar_municipio("  Guayaramerín ") == "GUAYARAMERIN"
    assert normalizar_municipio("Cercado Tarija") == "CERCADO TJ"
