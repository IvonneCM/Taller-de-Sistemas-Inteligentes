"""Disponibilidad de la API (TASK-040 / NFR-003).

- `/health`: la aplicacion esta viva (no consulta dependencias).
- `/health/ready`: ademas, la base de datos responde. Sirve como smoke test
  del despliegue y para ver rapido que dependencia fallo.
"""

import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["salud"])


@router.get("/health")
def health_check() -> dict:
    """Endpoint de verificacion de disponibilidad (soporta NFR-003)."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(respuesta: Response, db: Session = Depends(get_db)) -> dict:
    """200 si la base responde; 503 con `database: unavailable` si no."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.warning("Readiness: la base de datos no responde (%s)", type(error).__name__)
        respuesta.status_code = 503
        respuesta.headers["Retry-After"] = "5"
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
