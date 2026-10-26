"""Verificacion de TASK-009: 'test analogo a TASK-008 para
casos_epidemiologicos'."""

import warnings
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.etl.conectores.epidemiologia import (
    FUENTE_MINSALUD,
    FUENTE_MINSALUD_SEMANAL,
    fecha_cierre_periodo,
    fecha_fin_semana,
    ingerir_dengue_semanal,
    ingerir_epidemiologia_acumulada,
    leer_dengue_semanal_csv,
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


# ---------------------------------------------------------------------------
# Serie SEMANAL de dengue (TASK-009, decision 2 del reparto)
# ---------------------------------------------------------------------------

CSV_DENGUE_SEMANAL_MUESTRA = (
    "departamento,municipio,anio,semana_epidemiologica,casos_dengue\n"
    "BENI,GUAYARAMERIN,2026,1,3\n"
    "BENI,GUAYARAMERIN,2026,2,1\n"
    "BENI,GUAYARAMERIN,2026,3,0\n"
    "LA PAZ,IXIAMAS,2026,1,1\n"
    "LA PAZ,MUNICIPIO_INEXISTENTE,2026,1,5\n"
)

CSV_REAL = Path(__file__).resolve().parents[3] / "data" / "processed" / "dengue_municipal_semanal.csv"


def test_fecha_fin_semana_es_domingo_de_la_semana_iso():
    assert fecha_fin_semana(2026, 1) == date(2026, 1, 4)
    assert fecha_fin_semana(2026, 13) == date(2026, 3, 29)
    assert fecha_fin_semana(2026, 13) == fecha_cierre_periodo(2026, 13)


def test_leer_dengue_semanal_csv_rechaza_pii_y_valores_invalidos(tmp_path):
    con_pii = tmp_path / "pii.csv"
    con_pii.write_text("municipio,anio,semana_epidemiologica,casos_dengue,ci\nX,2026,1,1,123\n")
    with pytest.raises(ValueError, match="REQ-020"):
        leer_dengue_semanal_csv(str(con_pii))

    negativo = tmp_path / "neg.csv"
    negativo.write_text("municipio,anio,semana_epidemiologica,casos_dengue\nX,2026,1,-1\n")
    with pytest.raises(ValueError, match="negativo"):
        leer_dengue_semanal_csv(str(negativo))

    semana_mala = tmp_path / "sem.csv"
    semana_mala.write_text("municipio,anio,semana_epidemiologica,casos_dengue\nX,2026,60,1\n")
    with pytest.raises(ValueError, match="fuera de 1-53"):
        leer_dengue_semanal_csv(str(semana_mala))


@pytest.mark.skipif(not CSV_REAL.exists(), reason="serie semanal real no disponible")
def test_csv_real_de_dengue_semanal_cumple_lo_que_el_conector_espera():
    df = leer_dengue_semanal_csv(str(CSV_REAL))
    assert len(df) == 28 * 13
    assert df.groupby("municipio")["semana_epidemiologica"].nunique().eq(13).all()
    assert not df.duplicated(["municipio", "anio", "semana_epidemiologica"]).any()


def test_ingerir_dengue_semanal_inserta_una_fila_por_semana(db_session, tmp_path):
    ruta = tmp_path / "semanal.csv"
    ruta.write_text(CSV_DENGUE_SEMANAL_MUESTRA, encoding="utf-8")
    df = leer_dengue_semanal_csv(str(ruta))

    resultado = ingerir_dengue_semanal(db_session, df)

    assert resultado["insertados"] == 4          # 3 semanas Guayaramerin + 1 Ixiamas
    assert resultado["sin_municipio"] == 1       # fuera del catalogo: se descarta
    filas = db_session.query(CasoEpidemiologico).all()
    assert len(filas) == 4
    assert {f.fecha_reporte for f in filas if f.casos_confirmados == 3} == {fecha_fin_semana(2026, 1)}
    assert sum(f.casos_confirmados for f in filas) == 5  # 3+1+0+1: no se pierde ni inventa nada
    assert all(f.fuente == FUENTE_MINSALUD_SEMANAL and f.es_dato_imputado is False for f in filas)


def test_ingerir_dengue_semanal_no_duplica_en_segunda_corrida(db_session, tmp_path):
    ruta = tmp_path / "semanal.csv"
    ruta.write_text(CSV_DENGUE_SEMANAL_MUESTRA, encoding="utf-8")
    df = leer_dengue_semanal_csv(str(ruta))

    ingerir_dengue_semanal(db_session, df)
    segunda = ingerir_dengue_semanal(db_session, df)

    assert segunda["insertados"] == 0
    assert segunda["duplicados"] == 4


def test_ingerir_acumulado_de_dengue_advierte_riesgo_de_doble_conteo(db_session):
    df = pd.DataFrame([{"municipio": "GUAYARAMERIN", "anio": 2026,
                        "casos_dengue_acumulados_se1_13": 9, "estado_calidad": "valido"}])
    with pytest.warns(DeprecationWarning, match="duplicaria"):
        ingerir_epidemiologia_acumulada(db_session, df, "dengue")


def test_textos_de_fuente_caben_en_la_columna_varchar_100():
    # Un texto mas largo que el VARCHAR(100) de `fuente` solo falla contra
    # PostgreSQL real (SQLite no lo detecta): se verifica sin necesitar BD.
    assert len(FUENTE_MINSALUD) <= 100
    assert len(FUENTE_MINSALUD_SEMANAL) <= 100
    assert FUENTE_MINSALUD_SEMANAL != FUENTE_MINSALUD  # distintas: evita doble conteo
