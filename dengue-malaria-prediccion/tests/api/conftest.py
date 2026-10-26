"""Helpers de pytest para los tests de API."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models import Rol, Usuario

PASSWORD_TEST = "ClaveSegura123!"


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
