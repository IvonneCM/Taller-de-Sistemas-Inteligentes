"""Esquemas de TASK-022 (`GET /alertas`). REQ-005: cada alerta publicada
lleva su justificacion y al menos una variable explicativa."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.zonas import NivelRiesgo, VariableExplicativa


class AlertaOut(BaseModel):
    id: int
    prediccion_id: int
    municipio_id: int
    municipio: str
    departamento_id: int
    enfermedad_id: int
    enfermedad: str
    nivel_riesgo: NivelRiesgo
    probabilidad_pct: float
    umbral_aplicado: float
    fecha_emision: datetime
    fecha_estimada_riesgo: date
    justificacion: str
    variables_explicativas: list[VariableExplicativa]
