"""Fixtures de las pruebas de API: cliente HTTP que usa la misma sesion de BD
(transaccion con rollback) que el resto de la suite, y catalogo base."""

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from tests.api.helpers import crear_modelo

ROLES = ["autoridad", "sedes", "epidemiologo", "coordinador_municipal", "admin"]


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


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
