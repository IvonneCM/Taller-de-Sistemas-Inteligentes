"""Fixtures compartidas de pytest: una sesion de BD por test, dentro de una
transaccion que siempre se revierte al final (no ensucia la base de
desarrollo ni entre tests)."""

import os

import pytest
from fastapi.testclient import TestClient

# Debe definirse antes de importar app.core.security (lee el entorno al
# emitir/validar tokens, pero no al importar).
os.environ.setdefault("SECRET_KEY", "test-secret-key-solo-para-pytest-32-bytes")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("JWT_ISSUER", "dengue-malaria-api")

from app.core.database import SessionLocal, engine, get_db  # noqa: E402
from app.etl.seed_catalogo import seed as seed_catalogo  # noqa: E402
from app.main import app  # noqa: E402


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
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def catalogo(db_session):
    """Catalogo base (departamentos, enfermedades, municipios piloto) ya
    sembrado por `db_session`; seed() es idempotente y devuelve los objetos."""
    return seed_catalogo(db=db_session)
