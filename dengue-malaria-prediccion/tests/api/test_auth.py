"""Verificacion TASK-017: login JWT, refresh revocable y logout."""

import os
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import select

from app.core.security import decodificar_token
from app.models import RefreshToken


def test_login_valido_devuelve_access_y_refresh(client, crear_usuario, login):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    usuario_id = usuario.id

    respuesta = login(usuario.email, password)

    assert respuesta.status_code == 200
    body = respuesta.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 30 * 60

    payload = decodificar_token(body["access_token"], "access")
    assert payload["usuario_id"] == usuario_id
    assert payload["rol"] == "epidemiologo"
    assert payload["iss"] == "dengue-malaria-api"


def test_login_password_invalida_devuelve_401_generico(
    client, crear_usuario, login
):
    usuario, _ = crear_usuario("epi@test.local", "epidemiologo")

    respuesta = login(usuario.email, "password-incorrecta")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Credenciales invalidas"
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_login_usuario_inexistente_devuelve_mismo_401(client, login):
    respuesta = login("no-existe@test.local", "password-cualquiera")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Credenciales invalidas"


def test_refresh_rota_token_y_revoca_el_anterior(
    client, crear_usuario, login, db_session
):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    login_response = login(usuario.email, password)
    refresh_original = login_response.json()["refresh_token"]

    respuesta = client.post(
        "/auth/refresh", json={"refresh_token": refresh_original}
    )
    assert respuesta.status_code == 200
    nuevos_tokens = respuesta.json()
    assert nuevos_tokens["access_token"] != login_response.json()["access_token"]
    assert nuevos_tokens["refresh_token"] != refresh_original

    payload = decodificar_token(refresh_original, "refresh")
    registro = db_session.execute(
        select(RefreshToken).where(RefreshToken.jti == payload["jti"])
    ).scalar_one()
    assert registro.revocado_en is not None

    reutilizado = client.post(
        "/auth/refresh", json={"refresh_token": refresh_original}
    )
    assert reutilizado.status_code == 401

    vigente = client.post(
        "/auth/refresh", json={"refresh_token": nuevos_tokens["refresh_token"]}
    )
    assert vigente.status_code == 200


def test_logout_revoca_refresh(client, crear_usuario, login):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    tokens = login(usuario.email, password).json()

    respuesta = client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert respuesta.status_code == 204

    reutilizado = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reutilizado.status_code == 401


def test_logout_con_token_invalido_es_idempotente(client):
    respuesta = client.post(
        "/auth/logout", json={"refresh_token": "token-invalido"}
    )
    assert respuesta.status_code == 204


def test_access_token_no_sirve_como_refresh(client, crear_usuario, login):
    usuario, password = crear_usuario("epi@test.local", "epidemiologo")
    tokens = login(usuario.email, password).json()

    respuesta = client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert respuesta.status_code == 401


def test_login_es_case_insensitive_en_email(client, crear_usuario, login):
    usuario, password = crear_usuario("Epi@test.local", "epidemiologo")

    respuesta = login("epi@TEST.local", password)

    assert respuesta.status_code == 200


def test_token_sin_exp_devuelve_401(client, crear_usuario):
    usuario, _ = crear_usuario("epi@test.local", "epidemiologo")
    payload = {
        "sub": str(usuario.id),
        "rol": "epidemiologo",
        "tipo": "refresh",
        "jti": "token-sin-exp-de-prueba",
        "iat": datetime.now(timezone.utc),
        "iss": "dengue-malaria-api",
    }
    token = jwt.encode(
        payload,
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )

    respuesta = client.post(
        "/auth/refresh", json={"refresh_token": token}
    )

    assert respuesta.status_code == 401


def test_refresh_expirado_devuelve_401(client, crear_usuario):
    usuario, _ = crear_usuario("epi@test.local", "epidemiologo")
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario.id),
        "rol": "epidemiologo",
        "tipo": "refresh",
        "jti": "token-expirado-de-prueba",
        "iat": ahora - timedelta(days=8),
        "exp": ahora - timedelta(days=1),
        "iss": "dengue-malaria-api",
    }
    token = jwt.encode(
        payload,
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )

    respuesta = client.post(
        "/auth/refresh", json={"refresh_token": token}
    )

    assert respuesta.status_code == 401
