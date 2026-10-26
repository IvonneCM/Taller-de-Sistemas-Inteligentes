"""Verificacion TASK-018: RBAC en dependencias de FastAPI."""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import jwt

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models import Usuario


@pytest.fixture()
def protected_client(db_session):
    test_app = FastAPI()

    @test_app.get("/protegido")
    def protegido(usuario: Usuario = Depends(get_current_user)) -> dict:
        return {"email": usuario.email}

    @test_app.get("/solo-epidemiologo")
    def solo_epidemiologo(
        usuario: Usuario = Depends(require_role("epidemiologo")),
    ) -> dict:
        return {"email": usuario.email}

    def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_sin_token_devuelve_401(protected_client):
    respuesta = protected_client.get("/protegido")

    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_access_token_valido_permite_acceso(
    protected_client, crear_usuario, login
):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    token = login(usuario.email, password).json()["access_token"]

    respuesta = protected_client.get(
        "/protegido", headers=_headers(token)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "epi@test.local"


def test_refresh_token_no_sirve_como_access(
    protected_client, crear_usuario, login
):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    refresh = login(usuario.email, password).json()["refresh_token"]

    respuesta = protected_client.get(
        "/protegido", headers=_headers(refresh)
    )

    assert respuesta.status_code == 401


def test_access_expirado_devuelve_401(protected_client, crear_usuario):
    usuario, _ = crear_usuario("epi@test.local", "epidemiologo")
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario.id),
        "rol": "epidemiologo",
        "tipo": "access",
        "jti": "access-expirado-de-prueba",
        "iat": ahora - timedelta(minutes=60),
        "exp": ahora - timedelta(minutes=30),
        "iss": "dengue-malaria-api",
    }
    token = jwt.encode(
        payload,
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )

    respuesta = protected_client.get(
        "/protegido", headers=_headers(token)
    )

    assert respuesta.status_code == 401


def test_autoridad_recibe_403_en_endpoint_de_epidemiologo(
    protected_client, crear_usuario, login
):
    usuario, password = crear_usuario("autoridad@test.local", "autoridad")
    token = login(usuario.email, password).json()["access_token"]

    respuesta = protected_client.get(
        "/solo-epidemiologo", headers=_headers(token)
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "No autorizado para este recurso"


def test_epidemiologo_accede_a_endpoint_de_epidemiologo(
    protected_client, crear_usuario, login
):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    token = login(usuario.email, password).json()["access_token"]

    respuesta = protected_client.get(
        "/solo-epidemiologo", headers=_headers(token)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "epi@test.local"
