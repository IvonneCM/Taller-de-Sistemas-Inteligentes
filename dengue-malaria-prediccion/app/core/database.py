"""
Conexion a la base de datos (SQLAlchemy) y Base declarativa compartida por
todos los modelos ORM.

La URL de conexion viene de `app.core.config` (variable de entorno
DATABASE_URL, NFR-005: sin credenciales hardcodeadas).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

DATABASE_URL = get_settings().DATABASE_URL

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
