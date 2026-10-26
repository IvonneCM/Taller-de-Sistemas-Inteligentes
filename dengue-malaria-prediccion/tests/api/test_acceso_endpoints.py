"""Control de acceso de los endpoints de TASK-019 a 023 (REQ-007, REQ-019).

La emision y validacion de tokens se prueba en test_auth.py y test_rbac.py
(TASK-017/018); aqui solo se verifica que cada ruta aplique el rol correcto."""

import pytest

from tests.api.conftest import ROLES
from tests.api.helpers import cabeceras

RUTAS_PUBLICAS_AUTENTICADAS = ["/zonas/riesgo", "/alertas"]


def test_health_es_publico(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("get", "/zonas/riesgo"),
        ("get", "/zonas/1/prediccion"),
        ("get", "/zonas/1/historial"),
        ("get", "/alertas"),
        ("post", "/admin/umbrales"),
    ],
)
def test_sin_token_responde_401(client, metodo, ruta):
    assert getattr(client, metodo)(ruta).status_code == 401


@pytest.mark.parametrize("ruta", RUTAS_PUBLICAS_AUTENTICADAS)
@pytest.mark.parametrize("rol", ROLES)
def test_cualquier_rol_valido_puede_consultar(client, ruta, rol):
    assert client.get(ruta, headers=cabeceras(rol)).status_code == 200


def test_autoridad_recibe_403_en_endpoint_de_epidemiologo(client, guayaramerin):
    respuesta = client.get(
        f"/zonas/{guayaramerin.id}/historial", headers=cabeceras("autoridad")
    )
    assert respuesta.status_code == 403


def test_un_token_de_refresco_no_sirve_en_los_endpoints(client, db_session):
    from app.core.security import crear_refresh_token
    from tests.api.helpers import crear_usuario_con_rol

    usuario = crear_usuario_con_rol(db_session, "admin")
    refresco = crear_refresh_token(usuario.id, "admin").token
    respuesta = client.get("/zonas/riesgo", headers={"Authorization": f"Bearer {refresco}"})
    assert respuesta.status_code == 401
