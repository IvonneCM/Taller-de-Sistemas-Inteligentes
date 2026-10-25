"""Verificacion de TASK-008: 'test que ingiere un CSV/JSON de muestra y
valida que los registros aparecen en datos_climaticos con fuente
poblada'."""

import io

import pandas as pd

from app.etl.conectores.senamhi import (
    FUENTE_SENAMHI,
    ingerir_clima_diario,
    leer_clima_diario_csv,
    procesar_feature_api,
)
from app.models import DatoClimatico


CSV_MUESTRA = """municipio,fecha,temperatura_media,humedad_media,precipitacion_24h
GUAYARAMERIN,2026-01-14,30.85,72.0,0.6
IXIAMAS,2026-01-14,29.10,80.5,1.2
"""


def test_leer_clima_diario_csv_valida_columnas(tmp_path):
    ruta = tmp_path / "clima_muestra.csv"
    ruta.write_text(CSV_MUESTRA, encoding="utf-8")

    df = leer_clima_diario_csv(str(ruta))

    assert len(df) == 2
    assert set(df["municipio"]) == {"GUAYARAMERIN", "IXIAMAS"}


def test_ingerir_clima_diario_crea_filas_con_fuente_poblada(db_session, tmp_path):
    ruta = tmp_path / "clima_muestra.csv"
    ruta.write_text(CSV_MUESTRA, encoding="utf-8")
    df = leer_clima_diario_csv(str(ruta))

    resultado = ingerir_clima_diario(db_session, df)

    assert resultado["insertados"] == 2
    assert resultado["sin_municipio"] == 0
    assert resultado["duplicados"] == 0

    filas = db_session.query(DatoClimatico).all()
    assert len(filas) == 2
    for fila in filas:
        assert fila.fuente == FUENTE_SENAMHI
        assert fila.fuente != ""
        assert fila.es_dato_imputado is False


def test_ingerir_clima_diario_no_duplica_en_segunda_corrida(db_session, tmp_path):
    ruta = tmp_path / "clima_muestra.csv"
    ruta.write_text(CSV_MUESTRA, encoding="utf-8")
    df = leer_clima_diario_csv(str(ruta))

    ingerir_clima_diario(db_session, df)
    segunda = ingerir_clima_diario(db_session, df)

    assert segunda["insertados"] == 0
    assert segunda["duplicados"] == 2

    total = db_session.query(DatoClimatico).count()
    assert total == 2


def test_ingerir_clima_diario_descarta_municipio_fuera_de_catalogo(db_session):
    filas = [
        {
            "municipio": "MUNICIPIO_INEXISTENTE",
            "fecha": "2026-01-14",
            "temperatura_media": 25.0,
            "humedad_media": 70.0,
            "precipitacion_24h": 0.0,
        }
    ]

    resultado = ingerir_clima_diario(db_session, filas)

    assert resultado["insertados"] == 0
    assert resultado["sin_municipio"] == 1


def test_procesar_feature_api_filtra_variable_y_estacion_validas():
    estaciones = {"0-68-0-810201111863": "GUAYARAMERIN"}

    feature_valida = {
        "properties": {
            "name": "air_temperature",
            "wigos_station_identifier": "0-68-0-810201111863",
            "reportTime": "2026-01-14T14:00:00Z",
            "value": 30.85,
            "units": "Celsius",
        }
    }
    feature_variable_invalida = {
        "properties": {
            "name": "variable_no_usada",
            "wigos_station_identifier": "0-68-0-810201111863",
            "reportTime": "2026-01-14T14:00:00Z",
            "value": 1,
        }
    }
    feature_estacion_invalida = {
        "properties": {
            "name": "air_temperature",
            "wigos_station_identifier": "estacion-no-en-catalogo",
            "reportTime": "2026-01-14T14:00:00Z",
            "value": 1,
        }
    }

    resultado = procesar_feature_api(feature_valida, estaciones)
    assert resultado is not None
    assert resultado["municipio"] == "GUAYARAMERIN"
    assert resultado["fuente"] == FUENTE_SENAMHI

    assert procesar_feature_api(feature_variable_invalida, estaciones) is None
    assert procesar_feature_api(feature_estacion_invalida, estaciones) is None
