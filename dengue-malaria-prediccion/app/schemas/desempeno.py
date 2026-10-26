"""Esquemas de TASK-026 (`GET /modelo/desempeno`, REQ-016)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class ObjetivosDeDiseno(BaseModel):
    precision_espacial_pct: float
    anticipacion_dias: int
    nota: str


class DesempenoModelo(BaseModel):
    desde: date | None
    hasta: date | None
    enfermedad_id: int | None
    nivel_minimo: Literal["bajo", "medio", "alto"]
    ventana_correlacion_dias: int
    # Conteos
    predicciones_evaluadas: int
    predicciones_positivas: int
    aciertos: int
    falsas_alarmas: int
    brotes_confirmados: int
    brotes_detectados: int
    # Metricas: None cuando no hay base para calcularlas (nunca 0 inventado).
    precision_espacial_pct: float | None
    sensibilidad_pct: float | None
    anticipacion_dias_media: float | None
    anticipacion_dias_mediana: float | None
    aciertos_con_anticipacion_minima: int
    objetivos: ObjetivosDeDiseno
    estado: Literal["calculado", "sin_predicciones", "sin_brotes_confirmados"]
    nota: str
