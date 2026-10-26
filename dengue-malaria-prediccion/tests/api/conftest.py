"""Helpers de pytest para los tests de API."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models import Rol, Usuario
from tests.api import helpers
from tests.api.helpers import crear_modelo

PASSWORD_TEST = "ClaveSegura123!"
ROLES = ["autoridad", "sedes", "epidemiologo", "coordinador_municipal", "admin"]


@pytest.fixture()
def crear_usuario(db_session):
    """Crea un usuario de staff dentro de la transaccion del test."""

    def _crear(
        email: str,
        nombre_rol: str,
        password: str = PASSWORD_TEST,
        municipio_id: int | None = None,
    ):
        rol = db_session.execute(
            select(Rol).where(Rol.nombre == nombre_rol)
        ).scalar_one_or_none()
        if rol is None:
            rol = Rol(nombre=nombre_rol)
            db_session.add(rol)
            db_session.flush()

        usuario = Usuario(
            email=email,
            password_hash=hash_password(password),
            rol_id=rol.id,
            municipio_asignado_id=municipio_id,
        )
        db_session.add(usuario)
        db_session.flush()
        return usuario, password

    return _crear


@pytest.fixture()
def login(client):
    def _login(email: str, password: str):
        return client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )

    return _login


@pytest.fixture(autouse=True)
def _sesion_para_tokens(db_session):
    """Las cabeceras de `helpers.cabeceras(rol)` crean al usuario en la BD de
    la prueba: `get_current_user` lee el rol desde la BD, no desde el token."""
    helpers._SESION = db_session
    yield
    helpers._SESION = None


@pytest.fixture()
def dengue(catalogo):
    return catalogo["enfermedades"]["dengue"]


@pytest.fixture()
def malaria(catalogo):
    return catalogo["enfermedades"]["malaria"]


@pytest.fixture()
def guayaramerin(catalogo):
    return catalogo["municipios"]["GUAYARAMERIN"]


@pytest.fixture()
def ixiamas(catalogo):
    return catalogo["municipios"]["IXIAMAS"]


@pytest.fixture()
def modelo(db_session, dengue):
    return crear_modelo(db_session, dengue)
