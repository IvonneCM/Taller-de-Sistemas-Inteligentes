"""
Conexion a la base de datos (SQLAlchemy) y Base declarativa compartida por
todos los modelos ORM.

La URL de conexion viene de `app.core.config` (variable de entorno
DATABASE_URL, NFR-005: sin credenciales hardcodeadas).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
DATABASE_URL = _settings.DATABASE_URL

# TASK-040 (NFR-003): una base caida o lenta debe fallar rapido y de forma
# diagnosticable en vez de colgar la API. `hide_parameters` evita que los
# valores de una consulta (p. ej. un email) terminen en los logs de un error.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_timeout=_settings.DB_POOL_TIMEOUT_SECONDS,
    hide_parameters=True,
    connect_args={
        "connect_timeout": _settings.DB_CONNECT_TIMEOUT_SECONDS,
        "options": f"-c statement_timeout={_settings.DB_STATEMENT_TIMEOUT_MS}",
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesion y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
