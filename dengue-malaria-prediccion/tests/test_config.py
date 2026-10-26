"""TASK-003 (NFR-005): la configuracion sale del entorno, sin secretos en codigo."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

URL = "postgresql://u:p@localhost:5432/db"


def _settings(**kw) -> Settings:
    # _env_file=None: el test no depende de un .env local.
    return Settings(_env_file=None, **kw)


def test_falla_si_faltan_secretos(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        _settings()


def test_lee_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "3")
    s = _settings()
    assert s.DATABASE_URL == URL
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 3
    assert s.ALGORITHM == "HS256"
    assert s.ENVIRONMENT == "development"


def test_produccion_rechaza_secreto_debil(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "cambiar-por-una-clave-larga-y-aleatoria")
    with pytest.raises(ValidationError):
        _settings()
    monkeypatch.setenv("SECRET_KEY", "a" * 40)
    assert _settings().ENVIRONMENT == "production"
