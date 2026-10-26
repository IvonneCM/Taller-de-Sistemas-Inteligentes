"""Esquemas de respuesta de los endpoints de zonas (TASK-019, 020, 021).

El contenido por rol se decide en la capa de servicio/ruta, no en el
frontend (design.md §4, REQ-007): la vista resumida NO contiene los campos
tecnicos, no es la completa con campos en null.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

NivelRiesgo = Literal["bajo", "medio", "alto"]


class Centroide(BaseModel):
    lat: float
    lon: float


class ZonaRiesgo(BaseModel):
    """Una zona con su prediccion vigente, lista para el mapa de calor."""

    municipio_id: int
    municipio: str
    departamento_id: int
    departamento: str
    enfermedad_id: int
    enfermedad: str
    nivel_riesgo: NivelRiesgo
    probabilidad_pct: float
    nivel_confianza: NivelRiesgo
    fecha_generacion: datetime
    fecha_estimada_riesgo: date
    centroide: Centroide
    # GeoJSON (MultiPolygon, EPSG:4326). En la zona piloto es un cuadrado
    # REFERENCIAL, no el limite oficial del INE (ver seed_catalogo.py).
    geometria: dict


class VariableExplicativa(BaseModel):
    variable: str
    peso: float


class PrediccionResumen(BaseModel):
    enfermedad_id: int
    enfermedad: str
    nivel_riesgo: NivelRiesgo
    probabilidad_pct: float
    nivel_confianza: NivelRiesgo
    fecha_generacion: datetime
    fecha_estimada_riesgo: date


class PrediccionDetalle(PrediccionResumen):
    prediccion_id: int
    modelo_id: int
    modelo_nombre: str
    modelo_version: str
    variables_explicativas: list[VariableExplicativa]


class _ZonaPrediccionBase(BaseModel):
    municipio_id: int
    municipio: str
    departamento_id: int
    departamento: str


class ZonaPrediccionResumen(_ZonaPrediccionBase):
    vista: Literal["resumida"] = "resumida"
    predicciones: list[PrediccionResumen]


class ZonaPrediccionDetalle(_ZonaPrediccionBase):
    vista: Literal["completa"] = "completa"
    predicciones: list[PrediccionDetalle]


class BroteConfirmadoOut(BaseModel):
    id: int
    enfermedad_id: int
    enfermedad: str
    fecha_confirmacion: date
    fuente: str


class HistorialPrediccion(BaseModel):
    prediccion_id: int
    enfermedad_id: int
    enfermedad: str
    fecha_generacion: datetime
    fecha_estimada_riesgo: date
    nivel_riesgo: NivelRiesgo
    probabilidad_pct: float
    nivel_confianza: NivelRiesgo
    # Correlacion con brotes_confirmados (ver app/services/historial.py).
    # None/False cuando no hay un brote dentro de la ventana de la prediccion.
    brote_confirmado: bool
    brote_confirmado_id: int | None = None
    fecha_brote_confirmado: date | None = None
    # Dias entre la generacion de la prediccion y la confirmacion del brote
    # (insumo de NFR-002); solo cuando hay brote correlacionado.
    anticipacion_dias: int | None = None


class HistorialZona(_ZonaPrediccionBase):
    desde: date | None
    hasta: date | None
    ventana_correlacion_dias: int
    predicciones: list[HistorialPrediccion]
    brotes_confirmados: list[BroteConfirmadoOut]
