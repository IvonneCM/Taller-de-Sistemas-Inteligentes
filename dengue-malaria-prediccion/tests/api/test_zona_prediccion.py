"""Verificacion de TASK-020: 'test compara la respuesta para dos roles
distintos y confirma la diferencia de campos expuestos' (REQ-002, REQ-003,
REQ-004, REQ-007)."""

from datetime import datetime, timezone

import pytest

from tests.api.conftest import ROLES
from tests.api.helpers import (
    VARIABLES_EJEMPLO, cabeceras, crear_modelo, crear_prediccion,
)

AHORA = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)

CAMPOS_RESUMEN = {
    "enfermedad_id", "enfermedad", "nivel_riesgo", "probabilidad_pct",
    "nivel_confianza", "fecha_generacion", "fecha_estimada_riesgo",
}
CAMPOS_SOLO_TECNICOS = {
    "prediccion_id", "modelo_id", "modelo_nombre", "modelo_version",
    "variables_explicativas",
}


@pytest.fixture()
def zona_con_prediccion(db_session, dengue, modelo, guayaramerin):
    prediccion = crear_prediccion(
        db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
        nivel="alto", probabilidad=81.25, confianza="bajo", generada=AHORA, dias=24,
    )
    return guayaramerin, prediccion


def _url(zona):
    return f"/zonas/{zona.id}/prediccion"


def test_requiere_autenticacion(client, zona_con_prediccion):
    assert client.get(_url(zona_con_prediccion[0])).status_code == 401


def test_rol_tecnico_recibe_vista_completa_con_variables_ordenadas(
    client, zona_con_prediccion, modelo
):
    zona, prediccion = zona_con_prediccion

    cuerpo = client.get(_url(zona), headers=cabeceras("epidemiologo")).json()

    assert cuerpo["vista"] == "completa"
    assert cuerpo["municipio"] == "GUAYARAMERIN"
    assert cuerpo["departamento"] == "Beni"
    detalle = cuerpo["predicciones"][0]
    assert set(detalle) == CAMPOS_RESUMEN | CAMPOS_SOLO_TECNICOS
    assert detalle["prediccion_id"] == prediccion.id
    assert detalle["modelo_id"] == modelo.id
    assert detalle["modelo_nombre"] == "baseline_ejemplo"
    assert detalle["modelo_version"] == "v1"
    assert detalle["nivel_riesgo"] == "alto"
    assert detalle["probabilidad_pct"] == 81.25
    assert detalle["nivel_confianza"] == "bajo"
    assert detalle["fecha_estimada_riesgo"] == "2026-03-26"
    # REQ-004: al menos las 3 variables de mayor peso, tal como se guardaron.
    assert detalle["variables_explicativas"] == VARIABLES_EJEMPLO


def test_autoridad_recibe_vista_resumida_sin_campos_tecnicos(client, zona_con_prediccion):
    zona, _ = zona_con_prediccion

    cuerpo = client.get(_url(zona), headers=cabeceras("autoridad")).json()

    assert cuerpo["vista"] == "resumida"
    resumen = cuerpo["predicciones"][0]
    # Los campos tecnicos no vienen ni en null: no salen del servidor.
    assert set(resumen) == CAMPOS_RESUMEN
    # REQ-003 se cumple tambien en la vista resumida.
    assert resumen["probabilidad_pct"] == 81.25
    assert resumen["nivel_confianza"] == "bajo"


def test_dos_roles_ven_campos_distintos(client, zona_con_prediccion):
    zona, _ = zona_con_prediccion
    tecnico = client.get(_url(zona), headers=cabeceras("epidemiologo")).json()
    autoridad = client.get(_url(zona), headers=cabeceras("autoridad")).json()

    campos_t = set(tecnico["predicciones"][0])
    campos_a = set(autoridad["predicciones"][0])
    assert campos_a < campos_t
    assert campos_t - campos_a == CAMPOS_SOLO_TECNICOS


@pytest.mark.parametrize(
    "rol, vista",
    [("autoridad", "resumida"), ("sedes", "resumida"), ("coordinador_municipal", "resumida"),
     ("epidemiologo", "completa"), ("admin", "completa")],
)
def test_vista_segun_rol(client, zona_con_prediccion, rol, vista):
    zona, _ = zona_con_prediccion
    assert client.get(_url(zona), headers=cabeceras(rol)).json()["vista"] == vista


def test_todos_los_roles_pueden_consultar(client, zona_con_prediccion):
    zona, _ = zona_con_prediccion
    for rol in ROLES:
        assert client.get(_url(zona), headers=cabeceras(rol)).status_code == 200


def test_devuelve_solo_la_prediccion_vigente_por_enfermedad(
    client, db_session, dengue, malaria, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="bajo", probabilidad=5, generada=datetime(2026, 2, 16, tzinfo=timezone.utc))
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", probabilidad=88, generada=AHORA)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=malaria,
                     modelo=crear_modelo(db_session, malaria), nivel="medio",
                     probabilidad=40, generada=AHORA)

    cuerpo = client.get(_url(guayaramerin), headers=cabeceras("admin")).json()
    assert {p["enfermedad"]: p["probabilidad_pct"] for p in cuerpo["predicciones"]} == {
        "dengue": 88, "malaria": 40,
    }

    solo = client.get(
        f"{_url(guayaramerin)}?enfermedad_id={malaria.id}", headers=cabeceras("admin")
    ).json()
    assert [p["enfermedad"] for p in solo["predicciones"]] == ["malaria"]


def test_zona_inexistente_responde_404(client):
    assert client.get("/zonas/999999/prediccion", headers=cabeceras("admin")).status_code == 404


def test_zona_sin_predicciones_responde_404(client, guayaramerin):
    respuesta = client.get(_url(guayaramerin), headers=cabeceras("admin"))
    assert respuesta.status_code == 404
    assert "predicciones" in respuesta.json()["detail"]


def test_enfermedad_inexistente_responde_404(client, zona_con_prediccion):
    zona, _ = zona_con_prediccion
    respuesta = client.get(f"{_url(zona)}?enfermedad_id=9999", headers=cabeceras("admin"))
    assert respuesta.status_code == 404


def test_id_de_zona_no_numerico_responde_422(client):
    assert client.get("/zonas/abc/prediccion", headers=cabeceras("admin")).status_code == 422
