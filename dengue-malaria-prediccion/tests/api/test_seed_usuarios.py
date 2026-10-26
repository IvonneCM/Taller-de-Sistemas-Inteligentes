"""Verificacion del seed de desarrollo de TASK-017/TASK-018."""

import pytest
from sqlalchemy import func, select

from app.etl.seed_usuarios import USUARIOS_DEMO, delete, seed
from app.models import Usuario


def test_seed_crea_usuarios_demo_y_es_idempotente(db_session):
    primero = seed(password="ClaveDemo123!", db=db_session)
    assert set(primero) == {email for email, _, _ in USUARIOS_DEMO}
    assert all(estado == "creado" for estado in primero.values())

    segundo = seed(password="ClaveDemo123!", db=db_session)
    assert all(estado == "sin_cambios" for estado in segundo.values())

    cantidad = db_session.execute(
        select(func.count())
        .select_from(Usuario)
        .where(Usuario.email.like("%@demo.local"))
    ).scalar_one()
    assert cantidad == len(USUARIOS_DEMO)


def test_delete_elimina_solo_usuarios_demo(db_session, crear_usuario):
    usuario_real, _ = crear_usuario("persona@test.local", "autoridad")
    seed(password="ClaveDemo123!", db=db_session)

    resultado = delete(db=db_session)

    assert resultado["usuarios"] == len(USUARIOS_DEMO)
    quedan_demo = db_session.execute(
        select(Usuario).where(Usuario.email.like("%@demo.local"))
    ).scalars().all()
    assert quedan_demo == []
    assert db_session.get(Usuario, usuario_real.id) is not None


def test_seed_rechaza_entorno_produccion(db_session, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="production"):
        seed(password="ClaveDemo123!", db=db_session)
