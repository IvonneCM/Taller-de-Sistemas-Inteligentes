"""Fixtures compartidas de pytest: una sesion de BD por test, dentro de una
transaccion que siempre se revierte al final (no ensucia la base de
desarrollo ni entre tests)."""

import pytest

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
