"""Verificacion de la dependencia de autenticacion/RBAC (REQ-007, REQ-019):
un usuario con rol 'autoridad' recibe 403 en un endpoint restringido a
'epidemiologo'; sin token valido, 401."""

from datetime import timedelta

import pytest
from jose import jwt

from tests.api.conftest import ROLES
from tests.api.helpers import cabeceras, crear_token

RUTA_PROTEGIDA = "/zonas/riesgo"


def test_health_es_publico(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_sin_token_responde_401_con_www_authenticate(client):
    respuesta = client.get(RUTA_PROTEGIDA)
    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("esquema", ["Basic abc", "Bearer", "Bearer basura.no.jwt"])
def test_token_malformado_responde_401(client, esquema):
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": esquema}).status_code == 401


def test_token_expirado_responde_401(client):
    token = crear_token("admin", expira_en=timedelta(minutes=-1))
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_firmado_con_otra_clave_responde_401(client):
    falso = jwt.encode({"sub": "1", "rol": "admin"}, "otra-clave", algorithm="HS256")
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sin_firma_alg_none_responde_401(client):
    # Un token "alg: none" no debe aceptarse nunca.
    import base64
    import json

    def b64(datos):
        return base64.urlsafe_b64encode(json.dumps(datos).encode()).rstrip(b"=").decode()

    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': '1', 'rol': 'admin'})}."
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_de_refresco_no_sirve_como_acceso(client):
    assert client.get(RUTA_PROTEGIDA, headers=cabeceras("admin", type="refresh")).status_code == 401


@pytest.mark.parametrize("cambios", [{"rol": "superusuario"}, {"rol": None}])
def test_token_con_rol_desconocido_responde_401(client, cambios):
    token = jwt.encode(
        {"sub": "1", "exp": 4102444800, **cambios},
        __import__("os").environ["SECRET_KEY"],
        algorithm="HS256",
    )
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("sub", [None, "no-es-numero"])
def test_token_sin_sub_valido_responde_401(client, sub):
    payload = {"rol": "admin", "exp": 4102444800}
    if sub is not None:
        payload["sub"] = sub
    token = jwt.encode(payload, __import__("os").environ["SECRET_KEY"], algorithm="HS256")
    assert client.get(RUTA_PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_sin_secret_key_configurada_responde_500_y_no_acepta_tokens(client, monkeypatch):
    headers = cabeceras("admin")
    monkeypatch.delenv("SECRET_KEY")
    assert client.get(RUTA_PROTEGIDA, headers=headers).status_code == 500


@pytest.mark.parametrize("rol", ROLES)
def test_cualquier_rol_valido_puede_consultar_el_mapa(client, rol):
    assert client.get(RUTA_PROTEGIDA, headers=cabeceras(rol)).status_code == 200


def test_autoridad_recibe_403_en_endpoint_de_epidemiologo(client, guayaramerin):
    respuesta = client.get(
        f"/zonas/{guayaramerin.id}/historial", headers=cabeceras("autoridad")
    )
    assert respuesta.status_code == 403


def test_require_role_rechaza_roles_inexistentes_al_declararse():
    from app.api.deps import require_role

    with pytest.raises(ValueError):
        require_role("admin", "rol_inventado")
