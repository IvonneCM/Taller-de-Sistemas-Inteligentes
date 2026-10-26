"""Esquemas de TASK-047 (`GET /casos/resumen`): casos OBSERVADOS por zona.

Son conteos agregados por municipio y fecha de los boletines oficiales
(REQ-020: sin datos de pacientes). No son predicciones."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.schemas.zonas import Centroide


class CasosZona(BaseModel):
    municipio_id: int
    municipio: str
    departamento_id: int
    departamento: str
    enfermedad_id: int
    enfermedad: str
    # `semanal`: una fila por semana epidemiologica. `acumulado`: un solo total
    # del periodo (malaria: SE1-13, ver ADR-005); no hay serie semanal.
    granularidad: Literal["semanal", "acumulado"]
    total_casos: int
    desde: date
    hasta: date
    registros: int
    fuente: str
    centroide: Centroide
    # GeoJSON EPSG:4326; en la zona piloto es un cuadrado REFERENCIAL.
    geometria: dict
