"""`GET /panel/resumen`: indicadores de la pantalla de resumen.

Se verifica que dengue (semanal) y malaria (acumulado) NO se mezclen (ADR-005),
que sin datos no se inventen cifras y que cualquier rol autenticado pueda leerlo."""

from datetime import date, timedelta

import pytest

from app.etl.conectores.epidemiologia import FUENTE_MINSALUD, FUENTE_MINSALUD_SEMANAL
from app.models import CasoEpidemiologico
from tests.api.conftest import ROLES
from tests.api.helpers import cabeceras, crear_alerta, crear_prediccion


def _caso(db, municipio, enfermedad, fecha, casos, fuente):
    db.add(CasoEpidemiologico(
        municipio_id=municipio.id, enfermedad_id=enfermedad.id,
        fecha_reporte=fecha, casos_confirmados=casos, fuente=fuente,
    ))


@pytest.fixture()
def datos(db_session, dengue, malaria, guayaramerin, ixiamas, modelo):
    domingo = date(2026, 1, 4)
    for semana, (g, i) in enumerate([(3, 1), (5, 0), (2, 4)]):  # dengue semanal
        _caso(db_session, guayaramerin, dengue, domingo + timedelta(weeks=semana), g, FUENTE_MINSALUD_SEMANAL)
        _caso(db_session, ixiamas, dengue, domingo + timedelta(weeks=semana), i, FUENTE_MINSALUD_SEMANAL)
    _caso(db_session, guayaramerin, malaria, date(2026, 3, 29), 293, FUENTE_MINSALUD)  # acumulado
    _caso(db_session, ixiamas, malaria, date(2026, 3, 29), 156, FUENTE_MINSALUD)
    alta = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                            nivel="alto", probabilidad=82)
    crear_prediccion(db_session, municipio=ixiamas, enfermedad=dengue, modelo=modelo,
                     nivel="medio", probabilidad=45)
    crear_alerta(db_session, alta, umbral=70)
    db_session.flush()


def test_requiere_autenticacion(client):
    assert client.get("/panel/resumen").status_code == 401


@pytest.mark.parametrize("rol", ROLES)
def test_todos_los_roles_pueden_consultar(client, rol):
    assert client.get("/panel/resumen", headers=cabeceras(rol)).status_code == 200


def test_sin_datos_devuelve_ceros_y_listas_vacias(client):
    cuerpo = client.get("/panel/resumen", headers=cabeceras("autoridad")).json()
    assert cuerpo["alertas"] == {"emitidas": 0, "vigentes": 0}
    assert cuerpo["dengue"]["total_casos"] == 0
    assert cuerpo["dengue"]["serie_semanal"] == []
    assert cuerpo["dengue"]["ultima_semana"] is None and cuerpo["dengue"]["mayor_riesgo"] is None
    assert cuerpo["dengue"]["mayores_riesgos"] == []
    assert cuerpo["dengue"]["riesgo"] == {"alto": 0, "medio": 0, "bajo": 0, "total": 0}
    assert cuerpo["malaria"]["total_casos"] == 0 and cuerpo["malaria"]["fecha_corte"] is None


def test_dengue_se_suma_por_semana_y_nunca_con_malaria(client, datos):
    d = client.get("/panel/resumen", headers=cabeceras("autoridad")).json()["dengue"]
    assert [s["casos"] for s in d["serie_semanal"]] == [4, 5, 6]  # 3+1, 5+0, 2+4
    assert d["total_casos"] == 15  # no incluye los 449 de malaria
    assert d["ultima_semana"]["casos"] == 6 and d["semana_previa"]["casos"] == 5
    assert d["municipios_con_casos"] == 2
    assert d["top_municipios"][0]["municipio"] == "GUAYARAMERIN" and d["top_municipios"][0]["casos"] == 10


def test_malaria_es_un_acumulado_sin_serie_semanal(client, datos):
    m = client.get("/panel/resumen", headers=cabeceras("sedes")).json()["malaria"]
    assert m["total_casos"] == 449 and m["fecha_corte"] == "2026-03-29"
    assert [x["casos"] for x in m["top_municipios"]] == [293, 156]
    assert "serie_semanal" not in m


def test_riesgo_vigente_y_alertas(client, datos):
    cuerpo = client.get("/panel/resumen", headers=cabeceras("epidemiologo")).json()
    assert cuerpo["dengue"]["riesgo"] == {"alto": 1, "medio": 1, "bajo": 0, "total": 2}
    mayor = cuerpo["dengue"]["mayor_riesgo"]
    assert mayor["municipio"] == "GUAYARAMERIN" and mayor["probabilidad_pct"] == 82
    top = cuerpo["dengue"]["mayores_riesgos"]
    assert [z["municipio"] for z in top] == ["GUAYARAMERIN", "IXIAMAS"]  # de mayor a menor probabilidad
    assert top[0] == mayor
    assert cuerpo["alertas"]["emitidas"] == 1 and cuerpo["alertas"]["vigentes"] == 1


def test_incluye_la_advertencia_de_datos_provisionales(client):
    nota = client.get("/panel/resumen", headers=cabeceras("autoridad")).json()["nota"]
    assert "provisional" in nota and "no es una garant" in nota
