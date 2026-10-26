"""Punto de entrada de la API FastAPI.

Ver requirements.md y design.md antes de agregar endpoints.
"""

from fastapi import FastAPI

from app.api.routes import admin, alertas, campanas, casos, health, modelo, municipios, zonas
from app.api.routes.auth import router as auth_router
from app.core import observabilidad
from app.core.config import get_settings

observabilidad.configure_logging(get_settings().LOG_LEVEL)

# TASK-035: en produccion no se publica la documentacion interactiva ni el
# esquema OpenAPI (describen todos los endpoints y no hacen falta para operar).
_produccion = get_settings().ENVIRONMENT.lower() == "production"

app = FastAPI(
    title="Sistema de Prediccion Temprana de Brotes de Dengue/Malaria",
    version="0.1.0",
    docs_url=None if _produccion else "/docs",
    redoc_url=None if _produccion else "/redoc",
    openapi_url=None if _produccion else "/openapi.json",
)

observabilidad.instalar(app)

app.include_router(health.router)
app.include_router(zonas.router)
app.include_router(alertas.router)
app.include_router(casos.router)
app.include_router(admin.router)
app.include_router(auth_router)
app.include_router(campanas.router)
app.include_router(municipios.router)
app.include_router(modelo.router)
