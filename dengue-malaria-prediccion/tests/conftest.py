"""Fixtures compartidas de pytest: una sesion de BD por test, dentro de una
transaccion que siempre se revierte al final (no ensucia la base de
desarrollo ni entre tests)."""

import os

import pytest

# Clave JWT SOLO para pruebas (los tokens de test los firma tests/api/helpers.py).
# setdefault: no pisa una SECRET_KEY real del entorno del desarrollador.
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-no-usar-en-produccion")
os.environ.setdefault("ALGORITHM", "HS256")

from app.core.database import engine, SessionLocal
from app.etl.seed_catalogo import seed as seed_catalogo


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    seed_catalogo(db=session)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def catalogo(db_session):
    """Catalogo base (departamentos, enfermedades, municipios piloto) ya
    sembrado por `db_session`; seed() es idempotente y devuelve los objetos."""
    return seed_catalogo(db=db_session)
