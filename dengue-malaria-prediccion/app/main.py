"""Punto de entrada de la API FastAPI.

Ver requirements.md y design.md antes de agregar endpoints.
"""

from fastapi import FastAPI

from app.api.routes import admin, alertas, casos, health, zonas
from app.api.routes.auth import router as auth_router
from app.core import observabilidad
from app.core.config import get_settings

observabilidad.configure_logging(get_settings().LOG_LEVEL)

app = FastAPI(
    title="Sistema de Prediccion Temprana de Brotes de Dengue/Malaria",
    version="0.1.0",
)

observabilidad.instalar(app)

app.include_router(health.router)
app.include_router(zonas.router)
app.include_router(alertas.router)
app.include_router(casos.router)
app.include_router(admin.router)
app.include_router(auth_router)
