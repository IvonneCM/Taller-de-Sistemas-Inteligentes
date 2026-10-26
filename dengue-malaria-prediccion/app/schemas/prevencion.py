"""Contratos de TASK-024/025; porcentajes de presencia de casos, no gravedad."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.zonas import NivelRiesgo


class PrediccionPrevencion(BaseModel):
    prediccion_id: int
    municipio_id: int
    municipio: str
    departamento_id: int
    departamento: str
    enfermedad_id: int
    enfermedad: Literal["dengue"]
    horizonte_semanas: Literal[3]
    probabilidad_pct: float = Field(ge=0, le=100, allow_inf_nan=False)
    nivel_riesgo: NivelRiesgo
    nivel_confianza: NivelRiesgo
    fecha_generacion: datetime
    fecha_estimada_riesgo: date


class PrioridadCampana(PrediccionPrevencion):
    posicion: int = Field(ge=1)


class RecursosMunicipio(PrediccionPrevencion):
    nivel_atencion: Literal["PRIORITARIO", "PREVENTIVO", "RUTINARIO"]
    recomendaciones: list[str]
    nota: str
