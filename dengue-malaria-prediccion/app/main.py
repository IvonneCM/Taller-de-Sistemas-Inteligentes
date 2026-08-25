"""Punto de entrada de la API FastAPI.

Ver requirements.md y design.md antes de agregar endpoints.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Sistema de Prediccion Temprana de Brotes de Dengue/Malaria",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    """Endpoint de verificacion de disponibilidad (soporta NFR-003)."""
    return {"status": "ok"}
