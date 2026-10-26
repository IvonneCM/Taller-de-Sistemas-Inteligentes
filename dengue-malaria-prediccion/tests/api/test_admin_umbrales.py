"""Verificacion de TASK-023: 'test confirma que el cambio se refleja en la
siguiente llamada a evaluacion_alertas' (REQ-010). evaluacion_alertas es
TASK-015; aqui se verifica con `obtener_umbral`, su punto de lectura."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import UmbralConfiguracion
from app.services.umbrales import UMBRAL_POR_DEFECTO_PCT, obtener_umbral
from tests.api.conftest import ROLES
from tests.api.helpers import cabeceras

RUTA = "/admin/umbrales"


def _post(client, cuerpo, rol="admin"):
    return client.post(RUTA, json=cuerpo, headers=cabeceras(rol))


def _filas(db):
    return db.scalar(select(func.count()).select_from(UmbralConfiguracion))


@pytest.mark.parametrize("rol", [r for r in ROLES if r != "admin"])
def test_solo_admin_puede_configurar(client, dengue, rol):
    respuesta = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 60}, rol)
    assert respuesta.status_code == 403


def test_requiere_autenticacion(client, dengue):
    respuesta = client.post(RUTA, json={"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 60})
    assert respuesta.status_code == 401


def test_crea_umbral_general_de_la_enfermedad(client, db_session, dengue):
    respuesta = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 65.5})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["creado"] is True
    assert cuerpo["enfermedad"] == "dengue"
    assert cuerpo["departamento_id"] is None
    assert cuerpo["departamento"] is None
    assert cuerpo["umbral_probabilidad_pct"] == 65.5
    assert _filas(db_session) == 1


def test_crea_umbral_por_departamento(client, catalogo, dengue):
    beni = catalogo["departamentos"]["Beni"]
    respuesta = _post(
        client,
        {"enfermedad_id": dengue.id, "departamento_id": beni.id, "umbral_probabilidad_pct": 50},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["departamento"] == "Beni"


def test_repetir_el_mismo_umbral_actualiza_en_vez_de_duplicar(client, db_session, dengue):
    primero = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 60})
    segundo = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 80})

    assert primero.status_code == 201
    assert segundo.status_code == 200
    assert segundo.json()["creado"] is False
    assert segundo.json()["id"] == primero.json()["id"]
    assert segundo.json()["umbral_probabilidad_pct"] == 80
    assert _filas(db_session) == 1


def test_el_cambio_se_refleja_en_la_siguiente_evaluacion_sin_redeploy(
    client, db_session, catalogo, dengue
):
    beni = catalogo["departamentos"]["Beni"]
    la_paz = catalogo["departamentos"]["La Paz"]

    # Sin configuracion: umbral por defecto referencial.
    assert obtener_umbral(db_session, dengue.id, beni.id) == UMBRAL_POR_DEFECTO_PCT

    _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 55})
    assert obtener_umbral(db_session, dengue.id, beni.id) == Decimal("55.00")
    assert obtener_umbral(db_session, dengue.id, None) == Decimal("55.00")

    # Un umbral por departamento gana al general, solo para ese departamento.
    _post(client, {"enfermedad_id": dengue.id, "departamento_id": beni.id,
                   "umbral_probabilidad_pct": 40})
    assert obtener_umbral(db_session, dengue.id, beni.id) == Decimal("40.00")
    assert obtener_umbral(db_session, dengue.id, la_paz.id) == Decimal("55.00")

    # Un nuevo cambio se lee en la llamada siguiente (no hay cache).
    _post(client, {"enfermedad_id": dengue.id, "departamento_id": beni.id,
                   "umbral_probabilidad_pct": 90})
    assert obtener_umbral(db_session, dengue.id, beni.id) == Decimal("90.00")


def test_el_umbral_de_una_enfermedad_no_afecta_a_otra(client, db_session, dengue, malaria):
    _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": 30})
    assert obtener_umbral(db_session, malaria.id) == UMBRAL_POR_DEFECTO_PCT


@pytest.mark.parametrize("valor", [-0.1, 100.1, 1000])
def test_rechaza_umbrales_fuera_de_0_a_100(client, db_session, dengue, valor):
    respuesta = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": valor})
    assert respuesta.status_code == 422
    assert _filas(db_session) == 0


@pytest.mark.parametrize("valor", [0, 100])
def test_acepta_los_limites_0_y_100(client, dengue, valor):
    respuesta = _post(client, {"enfermedad_id": dengue.id, "umbral_probabilidad_pct": valor})
    assert respuesta.status_code == 201


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"umbral_probabilidad_pct": 60},
        {"enfermedad_id": 1},
        {"enfermedad_id": 1, "umbral_probabilidad_pct": "alto"},
        {"enfermedad_id": 1, "umbral_probabilidad_pct": 60, "campo_extra": "x"},
    ],
)
def test_cuerpo_invalido_responde_422(client, cuerpo):
    assert _post(client, cuerpo).status_code == 422


def test_enfermedad_o_departamento_inexistente_responde_404(client, db_session, dengue):
    assert _post(client, {"enfermedad_id": 9999, "umbral_probabilidad_pct": 60}).status_code == 404
    assert _post(
        client,
        {"enfermedad_id": dengue.id, "departamento_id": 9999, "umbral_probabilidad_pct": 60},
    ).status_code == 404
    assert _filas(db_session) == 0
