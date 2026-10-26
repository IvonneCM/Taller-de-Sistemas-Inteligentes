"""Fixtures compartidas de pytest: una sesion de BD por test, dentro de una
transaccion que siempre se revierte al final (no ensucia la base de
desarrollo ni entre tests).

Cada test parte de las tablas de DATOS vacias aunque la base de desarrollo ya
tenga datos de demostracion (app/etl/seed_demo.py): el vaciado se hace DENTRO de
la transaccion del test y se revierte con ella, asi que no borra nada de verdad."""

import os

import pytest
from fastapi.testclient import TestClient

# Debe definirse antes de importar app.core.security (lee el entorno al
# emitir/validar tokens, pero no al importar).
os.environ.setdefault("SECRET_KEY", "test-secret-key-solo-para-pytest-32-bytes")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("JWT_ISSUER", "dengue-malaria-api")

from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal, engine, get_db  # noqa: E402
from app.etl.seed_catalogo import seed as seed_catalogo  # noqa: E402
from app.main import app  # noqa: E402


# Tablas que llena la demostracion o la ingesta. Orden: hijas antes que padres.
# El catalogo (departamentos, enfermedades, municipios, roles) se conserva.
TABLAS_DE_DATOS = (
    "alertas", "predicciones", "brotes_confirmados", "umbrales_configuracion",
    "refresh_tokens", "usuarios", "modelos", "casos_epidemiologicos", "datos_climaticos",
)


def pytest_sessionstart(session):
    # Aunque todo se revierte, nunca se corre la suite contra una base de produccion.
    if get_settings().ENVIRONMENT == "production":
        pytest.exit("Las pruebas no se ejecutan con ENVIRONMENT=production.", returncode=2)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    for tabla in TABLAS_DE_DATOS:
        connection.execute(text(f"DELETE FROM {tabla}"))

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
