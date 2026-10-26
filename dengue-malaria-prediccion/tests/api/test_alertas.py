"""Verificacion de TASK-022: 'test de integracion filtra correctamente por
parametros de consulta' (REQ-009; REQ-005 para la justificacion)."""

from datetime import datetime, timedelta, timezone

import pytest

from tests.api.conftest import ROLES
from tests.api.helpers import (
    VARIABLES_EJEMPLO, cabeceras, crear_alerta, crear_modelo, crear_prediccion,
)

BASE = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def alertas(db_session, dengue, malaria, modelo, guayaramerin, ixiamas):
    modelo_malaria = crear_modelo(db_session, malaria)
    p_gua = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue,
                             modelo=modelo, probabilidad=85, generada=BASE)
    p_ixi = crear_prediccion(db_session, municipio=ixiamas, enfermedad=dengue,
                             modelo=modelo, probabilidad=92, generada=BASE)
    p_mal = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=malaria,
                             modelo=modelo_malaria, probabilidad=75, generada=BASE)
    return {
        "gua_dengue": crear_alerta(db_session, p_gua, umbral=70,
                                   justificacion="Casos recientes en alza.",
                                   emitida=BASE),
        "ixi_dengue": crear_alerta(db_session, p_ixi, umbral=70,
                                   emitida=BASE + timedelta(days=7)),
        "gua_malaria": crear_alerta(db_session, p_mal, umbral=60,
                                    emitida=BASE + timedelta(days=14)),
    }


def test_requiere_autenticacion(client):
    assert client.get("/alertas").status_code == 401


@pytest.mark.parametrize("rol", ROLES)
def test_todos_los_roles_pueden_listar(client, alertas, rol):
    assert client.get("/alertas", headers=cabeceras(rol)).status_code == 200


def test_sin_alertas_devuelve_lista_vacia(client):
    assert client.get("/alertas", headers=cabeceras("autoridad")).json() == []


def test_lista_las_mas_recientes_primero_con_justificacion_y_variables(client, alertas):
    cuerpo = client.get("/alertas", headers=cabeceras("autoridad")).json()

    assert [a["id"] for a in cuerpo] == [
        alertas["gua_malaria"].id, alertas["ixi_dengue"].id, alertas["gua_dengue"].id,
    ]
    gua = cuerpo[2]
    assert gua["municipio"] == "GUAYARAMERIN"
    assert gua["enfermedad"] == "dengue"
    assert gua["nivel_riesgo"] == "alto"
    assert gua["probabilidad_pct"] == 85
    assert gua["umbral_aplicado"] == 70
    assert gua["justificacion"] == "Casos recientes en alza."
    # REQ-005: nunca una alerta "vacia": siempre al menos una variable.
    assert gua["variables_explicativas"] == VARIABLES_EJEMPLO
    for alerta in cuerpo:
        assert alerta["justificacion"].strip()
        assert len(alerta["variables_explicativas"]) >= 1


def test_filtra_por_zona(client, alertas, guayaramerin):
    cuerpo = client.get(
        f"/alertas?municipio_id={guayaramerin.id}", headers=cabeceras("sedes")
    ).json()
    assert {a["id"] for a in cuerpo} == {
        alertas["gua_dengue"].id, alertas["gua_malaria"].id,
    }


def test_filtra_por_enfermedad(client, alertas, malaria):
    cuerpo = client.get(
        f"/alertas?enfermedad_id={malaria.id}", headers=cabeceras("sedes")
    ).json()
    assert [a["id"] for a in cuerpo] == [alertas["gua_malaria"].id]


def test_filtra_por_rango_de_fechas_de_emision(client, alertas):
    cuerpo = client.get(
        "/alertas?desde=2026-03-05&hasta=2026-03-12", headers=cabeceras("sedes")
    ).json()
    assert [a["id"] for a in cuerpo] == [alertas["ixi_dengue"].id]

    solo_desde = client.get("/alertas?desde=2026-03-10", headers=cabeceras("sedes")).json()
    assert [a["id"] for a in solo_desde] == [alertas["gua_malaria"].id]

    solo_hasta = client.get("/alertas?hasta=2026-03-02", headers=cabeceras("sedes")).json()
    assert [a["id"] for a in solo_hasta] == [alertas["gua_dengue"].id]


def test_combina_filtros(client, alertas, guayaramerin, dengue):
    cuerpo = client.get(
        f"/alertas?municipio_id={guayaramerin.id}&enfermedad_id={dengue.id}",
        headers=cabeceras("sedes"),
    ).json()
    assert [a["id"] for a in cuerpo] == [alertas["gua_dengue"].id]


def test_paginacion(client, alertas):
    pagina_1 = client.get("/alertas?limite=2", headers=cabeceras("sedes")).json()
    pagina_2 = client.get("/alertas?limite=2&desplazamiento=2", headers=cabeceras("sedes")).json()
    assert len(pagina_1) == 2
    assert len(pagina_2) == 1
    assert {a["id"] for a in pagina_1}.isdisjoint({a["id"] for a in pagina_2})


@pytest.mark.parametrize("consulta", ["limite=0", "limite=501", "desplazamiento=-1", "limite=abc"])
def test_parametros_de_paginacion_invalidos_responden_422(client, consulta):
    assert client.get(f"/alertas?{consulta}", headers=cabeceras("sedes")).status_code == 422


def test_rango_invertido_responde_422(client):
    respuesta = client.get("/alertas?desde=2026-04-01&hasta=2026-03-01", headers=cabeceras("sedes"))
    assert respuesta.status_code == 422


def test_no_publica_alertas_cuya_prediccion_no_tiene_variables_explicativas(
    client, db_session, dengue, modelo, guayaramerin, ixiamas
):
    # Segunda barrera de REQ-005: una fila incompleta no debe llegar al panel.
    # (El CHECK de la BD ya exige que `variables_explicativas` sea una lista.)
    sin_variables = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue,
                                     modelo=modelo, variables=[], generada=BASE)
    completa = crear_prediccion(db_session, municipio=ixiamas, enfermedad=dengue,
                                modelo=modelo, generada=BASE + timedelta(days=1))
    crear_alerta(db_session, sin_variables)
    buena = crear_alerta(db_session, completa)

    cuerpo = client.get("/alertas", headers=cabeceras("autoridad")).json()

    assert [a["id"] for a in cuerpo] == [buena.id]
