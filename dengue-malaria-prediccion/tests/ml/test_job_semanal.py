"""Verificacion de TASK-016: 'ejecucion manual del job confirma insercion de
nuevas filas en predicciones con fecha correcta'."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from app.ml import job_semanal
from app.models import Alerta, Modelo, Prediccion
from app.services.umbrales import configurar_umbral

LUNES = datetime(2026, 11, 2, 6, 17, tzinfo=timezone.utc)   # lunes de la semana ISO 45
PILOTO = {"GUAYARAMERIN", "IXIAMAS", "PALOS BLANCOS", "SAN BUENAVENTURA"}


def _contar(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def test_la_primera_ejecucion_registra_el_modelo_e_inserta_predicciones_con_la_fecha_correcta(db_session, catalogo):
    resumen = job_semanal.ejecutar(db_session, fecha_generacion=LUNES)

    assert resumen["omitida"] is False and resumen["modelo_creado"] is True
    predicciones = db_session.execute(select(Prediccion)).scalars().all()
    assert len(predicciones) == resumen["insertadas"] > 0
    assert {p.municipio.nombre for p in predicciones} <= PILOTO
    for p in predicciones:
        assert p.fecha_generacion == LUNES                                  # la fecha pedida, no "ahora"
        assert p.fecha_estimada_riesgo == date(2026, 11, 2) + timedelta(days=21)   # horizonte de 21 dias (REQ-002)
        assert p.enfermedad.nombre == "dengue" and len(p.variables_explicativas) >= 1
    assert _contar(db_session, Modelo) == 1


def test_un_reintento_la_misma_semana_no_duplica(db_session, catalogo):
    job_semanal.ejecutar(db_session, fecha_generacion=LUNES)
    antes = _contar(db_session, Prediccion)

    segundo = job_semanal.ejecutar(db_session, fecha_generacion=LUNES + timedelta(days=3))   # jueves, misma semana ISO

    assert segundo["omitida"] is True and segundo["insertadas"] == 0 and "semana ISO" in segundo["motivo"]
    assert segundo["modelo_creado"] is False
    assert _contar(db_session, Prediccion) == antes


def test_la_semana_siguiente_agrega_una_nueva_tanda_sin_tocar_la_anterior(db_session, catalogo):
    primera = job_semanal.ejecutar(db_session, fecha_generacion=LUNES)
    antes = db_session.execute(select(Prediccion.id, Prediccion.probabilidad_pct).order_by(Prediccion.id)).all()

    segunda = job_semanal.ejecutar(db_session, fecha_generacion=LUNES + timedelta(days=7))

    assert segunda["omitida"] is False and segunda["insertadas"] == primera["insertadas"]
    todas = db_session.execute(select(Prediccion).order_by(Prediccion.id)).scalars().all()
    assert len(todas) == 2 * primera["insertadas"]
    # Las predicciones de la primera semana siguen intactas (NFR-009).
    assert db_session.execute(select(Prediccion.id, Prediccion.probabilidad_pct).order_by(Prediccion.id).limit(len(antes))).all() == antes
    assert {p.fecha_generacion for p in todas} == {LUNES, LUNES + timedelta(days=7)}


def test_forzar_agrega_otra_tanda_en_la_misma_semana(db_session, catalogo):
    job_semanal.ejecutar(db_session, fecha_generacion=LUNES)
    forzada = job_semanal.ejecutar(db_session, fecha_generacion=LUNES, forzar=True)
    assert forzada["omitida"] is False and forzada["insertadas"] > 0


def test_evalua_las_alertas_con_el_umbral_vigente(db_session, catalogo):
    dengue = catalogo["enfermedades"]["dengue"]
    # Con el umbral por defecto (70 %) ninguna alerta; con 40 % alertan las zonas sobre ese valor.
    sin = job_semanal.ejecutar(db_session, fecha_generacion=LUNES)
    assert sin["alertas"] == 0
    configurar_umbral(db_session, enfermedad_id=dengue.id, departamento_id=None, umbral_probabilidad_pct=40)

    con = job_semanal.ejecutar(db_session, fecha_generacion=LUNES + timedelta(days=7))

    alertas = db_session.execute(select(Alerta)).scalars().all()
    assert con["alertas"] == len(alertas) > 0
    for a in alertas:
        assert a.prediccion.probabilidad_pct >= 40 and a.justificacion.strip()


def test_acepta_una_fecha_sin_hora_ni_zona(db_session, catalogo):
    resumen = job_semanal.ejecutar(db_session, fecha_generacion=date(2026, 11, 2))
    assert resumen["fecha_generacion"].startswith("2026-11-02T00:00:00")


@pytest.mark.parametrize("momento, lunes", [
    (datetime(2026, 11, 2, 0, 0, tzinfo=timezone.utc), date(2026, 11, 2)),
    (datetime(2026, 11, 8, 23, 59, tzinfo=timezone.utc), date(2026, 11, 2)),   # domingo
    (datetime(2026, 11, 9, 0, 0, tzinfo=timezone.utc), date(2026, 11, 9)),
])
def test_inicio_de_semana_iso(momento, lunes):
    assert job_semanal.inicio_de_semana_iso(momento).date() == lunes


def test_sin_los_artefactos_del_modelo_falla_con_un_mensaje_claro(db_session, catalogo, tmp_path):
    with pytest.raises(FileNotFoundError, match="entrenar"):
        job_semanal.ejecutar(db_session, fecha_generacion=LUNES, directorio=tmp_path)


def test_el_comando_sale_con_0_y_con_1_si_falla(db_session, catalogo, capsys):
    with patch.object(job_semanal, "SessionLocal", return_value=db_session):
        assert job_semanal.main(["--fecha", "2026-11-02T06:17:00+00:00"]) == 0
        assert "Predicciones insertadas" in capsys.readouterr().out
        assert job_semanal.main(["--fecha", "2026-11-03T06:17:00+00:00"]) == 0          # misma semana
        assert "Sin cambios" in capsys.readouterr().out
    with patch.object(job_semanal, "SessionLocal", return_value=db_session), \
         patch.object(job_semanal, "ejecutar", side_effect=RuntimeError("base caida")):
        assert job_semanal.main([]) == 1


def test_una_fecha_invalida_se_rechaza():
    with pytest.raises(SystemExit):
        job_semanal.main(["--fecha", "mañana"])
