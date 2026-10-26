"""Verificacion de TASK-047: 'test de integracion con casos de dengue
semanales y de malaria acumulados' (REQ-008, REQ-014, ADR-005)."""

from datetime import date, timedelta

import pytest

from app.etl.conectores.epidemiologia import FUENTE_MINSALUD, FUENTE_MINSALUD_SEMANAL
from app.models import CasoEpidemiologico
from tests.api.conftest import ROLES
from tests.api.helpers import cabeceras


def _caso(db, municipio, enfermedad, fecha, casos, fuente):
    db.add(CasoEpidemiologico(
        municipio_id=municipio.id, enfermedad_id=enfermedad.id,
        fecha_reporte=fecha, casos_confirmados=casos, fuente=fuente,
    ))


@pytest.fixture()
def casos(db_session, dengue, malaria, guayaramerin, ixiamas):
    domingo = date(2026, 1, 4)
    for semana, n in enumerate([3, 5, 2]):  # dengue semanal en Guayaramerin
        _caso(db_session, guayaramerin, dengue, domingo + timedelta(weeks=semana), n, FUENTE_MINSALUD_SEMANAL)
    _caso(db_session, guayaramerin, malaria, date(2026, 4, 5), 40, FUENTE_MINSALUD)  # acumulado
    _caso(db_session, ixiamas, malaria, date(2026, 4, 5), 20, FUENTE_MINSALUD)
    db_session.flush()


def _por_clave(cuerpo):
    return {(f["municipio"], f["enfermedad"]): f for f in cuerpo}


def test_requiere_autenticacion(client):
    assert client.get("/casos/resumen").status_code == 401


@pytest.mark.parametrize("rol", ROLES)
def test_todos_los_roles_pueden_consultar(client, rol):
    assert client.get("/casos/resumen", headers=cabeceras(rol)).status_code == 200


def test_sin_casos_devuelve_lista_vacia(client):
    assert client.get("/casos/resumen", headers=cabeceras("autoridad")).json() == []


def test_dengue_es_semanal_y_malaria_acumulado(client, casos):
    cuerpo = client.get("/casos/resumen", headers=cabeceras("autoridad")).json()
    filas = _por_clave(cuerpo)

    dengue = filas[("GUAYARAMERIN", "dengue")]
    assert dengue["granularidad"] == "semanal"
    assert dengue["total_casos"] == 10
    assert dengue["registros"] == 3
    assert (dengue["desde"], dengue["hasta"]) == ("2026-01-04", "2026-01-18")
    assert dengue["fuente"] == FUENTE_MINSALUD_SEMANAL

    malaria = filas[("GUAYARAMERIN", "malaria")]
    assert malaria["granularidad"] == "acumulado"
    assert malaria["total_casos"] == 40
    assert malaria["registros"] == 1
    assert malaria["fuente"] == FUENTE_MINSALUD
    assert filas[("IXIAMAS", "malaria")]["total_casos"] == 20


def test_incluye_geometria_y_centroide_para_el_mapa(client, casos):
    fila = _por_clave(client.get("/casos/resumen", headers=cabeceras("sedes")).json())[
        ("IXIAMAS", "malaria")
    ]
    assert fila["geometria"]["type"] == "MultiPolygon"
    assert abs(fila["centroide"]["lat"] - (-13.77117)) < 0.01
    assert fila["departamento"] == "La Paz"


def test_filtra_por_enfermedad_y_ordena_por_casos(client, casos, malaria):
    cuerpo = client.get(
        f"/casos/resumen?enfermedad_id={malaria.id}", headers=cabeceras("sedes")
    ).json()
    assert [(f["municipio"], f["total_casos"]) for f in cuerpo] == [
        ("GUAYARAMERIN", 40), ("IXIAMAS", 20),
    ]


def test_nunca_suma_filas_semanales_con_acumuladas_de_la_misma_enfermedad(
    client, db_session, dengue, guayaramerin
):
    for semana in range(2):
        _caso(db_session, guayaramerin, dengue, date(2026, 1, 4) + timedelta(weeks=semana), 4, FUENTE_MINSALUD_SEMANAL)
    _caso(db_session, guayaramerin, dengue, date(2026, 4, 5), 500, FUENTE_MINSALUD)
    db_session.flush()

    cuerpo = client.get("/casos/resumen", headers=cabeceras("admin")).json()

    assert len(cuerpo) == 1
    assert cuerpo[0]["granularidad"] == "semanal" and cuerpo[0]["total_casos"] == 8


def test_enfermedad_inexistente_responde_404(client):
    assert client.get("/casos/resumen?enfermedad_id=9999", headers=cabeceras("admin")).status_code == 404


def test_no_expone_datos_de_pacientes(client, casos):
    campos = set(client.get("/casos/resumen", headers=cabeceras("admin")).json()[0])
    assert campos == {
        "municipio_id", "municipio", "departamento_id", "departamento", "enfermedad_id",
        "enfermedad", "granularidad", "total_casos", "desde", "hasta", "registros",
        "fuente", "centroide", "geometria",
    }
