"""
Conexion a la base de datos (SQLAlchemy) y Base declarativa compartida por
todos los modelos ORM.

Nota de alcance: TASK-003 (Ignacio) formalizara la lectura de variables de
entorno en app/core/config.py (Settings con pydantic-settings, validacion,
etc.). Este modulo solo provee lo minimo que TASK-005/006/007 necesitan para
definir modelos y que Alembic pueda generar/aplicar migraciones: la Base
declarativa, el engine y una sesion. Lee DATABASE_URL directamente de la
variable de entorno (NFR-005: sin credenciales hardcodeadas) para no
duplicar logica que luego viva en config.py.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no esta definida. Copiar .env.example como .env y "
        "completar con credenciales reales (nunca hardcodear, ver "
        "CLAUDE.md regla 6)."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesion y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
