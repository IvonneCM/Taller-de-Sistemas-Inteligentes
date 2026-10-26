"""Verificacion de TASK-009: 'test analogo a TASK-008 para
casos_epidemiologicos'."""

import pandas as pd
import pytest

from app.etl.conectores.epidemiologia import (
    FUENTE_MINSALUD,
    fecha_cierre_periodo,
    ingerir_epidemiologia_acumulada,
    leer_epidemiologia_municipal_csv,
)
from app.models import CasoEpidemiologico


CSV_DENGUE_MUESTRA = (
    "departamento,municipio,anio,casos_dengue_acumulados_se1_13,periodo,"
    "fuente,estado_calidad,regla_aplicada,motivo_qc\n"
    "BENI,GUAYARAMERIN,2026,9,SE 1-13,Min. Salud,valido,,\n"
    "LA PAZ,IXIAMAS,2026,3,SE 1-13,Min. Salud,valido,,\n"
    # fila rechazada por el pipeline de Linea Base (casos invalidos) ->
    # no debe ingerirse, ni siquiera disfrazada de cero.
    "BENI,MUNICIPIO_RECHAZADO,2026,-1,SE 1-13,Min. Salud,rechazado,EPI-01,casos_negativos\n"
)


def test_leer_epidemiologia_municipal_csv_rechaza_columnas_pii(tmp_path):
    ruta = tmp_path / "dengue_con_pii.csv"
    ruta.write_text(
        "municipio,anio,estado_calidad,casos_dengue_acumulados_se1_13,ci\n"
        "GUAYARAMERIN,2026,valido,9,1234567\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REQ-020"):
        leer_epidemiologia_municipal_csv(str(ruta), "dengue")


def test_ingerir_epidemiologia_acumulada_inserta_solo_filas_validas(db_session, tmp_path):
    ruta = tmp_path / "dengue_muestra.csv"
    ruta.write_text(CSV_DENGUE_MUESTRA, encoding="utf-8")
    df = leer_epidemiologia_municipal_csv(str(ruta), "dengue")

    resultado = ingerir_epidemiologia_acumulada(db_session, df, "dengue")

    assert resultado["insertados"] == 2
    assert resultado["rechazados_por_fuente"] == 1  # MUNICIPIO_RECHAZADO
    assert resultado["sin_municipio"] == 0

    filas = db_session.query(CasoEpidemiologico).all()
    assert len(filas) == 2
    for fila in filas:
        assert fila.fuente == FUENTE_MINSALUD
        assert fila.es_dato_imputado is False
        # TASK-009: nunca una fecha_reporte por semana individual inventada;
        # siempre el mismo cierre de periodo (SE13) para el mismo anio.
        assert fila.fecha_reporte == fecha_cierre_periodo(2026)


def test_ingerir_epidemiologia_acumulada_no_duplica_en_segunda_corrida(db_session, tmp_path):
    ruta = tmp_path / "dengue_muestra.csv"
    ruta.write_text(CSV_DENGUE_MUESTRA, encoding="utf-8")
    df = leer_epidemiologia_municipal_csv(str(ruta), "dengue")

    ingerir_epidemiologia_acumulada(db_session, df, "dengue")
    segunda = ingerir_epidemiologia_acumulada(db_session, df, "dengue")

    assert segunda["insertados"] == 0
    assert segunda["duplicados"] == 2


def test_ingerir_epidemiologia_descarta_municipio_fuera_de_catalogo(db_session):
    df = pd.DataFrame(
        [
            {
                "municipio": "MUNICIPIO_INEXISTENTE",
                "anio": 2026,
                "casos_dengue_acumulados_se1_13": 5,
                "estado_calidad": "valido",
            }
        ]
    )

    resultado = ingerir_epidemiologia_acumulada(db_session, df, "dengue")

    assert resultado["insertados"] == 0
    assert resultado["sin_municipio"] == 1


def test_fecha_cierre_periodo_es_el_domingo_de_la_se13():
    cierre = fecha_cierre_periodo(2026, 13)
    assert cierre.isocalendar().week == 13
    assert cierre.isocalendar().weekday == 7  # domingo
