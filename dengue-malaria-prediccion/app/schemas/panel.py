"""Esquemas de `GET /panel/resumen`: indicadores para la pantalla de resumen.

Todo son agregados por municipio y fecha (REQ-020: sin datos de pacientes).
Los casos son OBSERVADOS (boletines); el riesgo es la PREDICCION vigente."""

from datetime import date, datetime

from pydantic import BaseModel


class SemanaCasos(BaseModel):
    fecha: date  # domingo de la semana ISO (misma convencion que `casos_epidemiologicos`)
    semana: int
    casos: int


class MunicipioCasos(BaseModel):
    municipio_id: int
    municipio: str
    departamento: str
    casos: int


class DistribucionRiesgo(BaseModel):
    alto: int
    medio: int
    bajo: int
    total: int


class MayorRiesgo(BaseModel):
    municipio_id: int
    municipio: str
    departamento: str
    nivel_riesgo: str
    probabilidad_pct: float
    fecha_estimada_riesgo: date | None


class ResumenAlertas(BaseModel):
    emitidas: int
    vigentes: int


class ResumenDengue(BaseModel):
    municipios_con_casos: int
    total_casos: int
    # Serie semanal nacional (suma de los municipios cargados). La ultima semana
    # es PROVISIONAL: los boletines la corrigen al alza despues.
    serie_semanal: list[SemanaCasos]
    ultima_semana: SemanaCasos | None
    semana_previa: SemanaCasos | None
    top_municipios: list[MunicipioCasos]
    riesgo: DistribucionRiesgo
    mayor_riesgo: MayorRiesgo | None
    # Las 5 zonas con mayor probabilidad (la primera es `mayor_riesgo`).
    mayores_riesgos: list[MayorRiesgo]
    fecha_prediccion: datetime | None


class ResumenMalaria(BaseModel):
    municipios_con_casos: int
    total_casos: int
    fecha_corte: date | None  # malaria es un acumulado, no una serie semanal (ADR-005)
    top_municipios: list[MunicipioCasos]


class PanelResumen(BaseModel):
    generado: datetime
    alertas: ResumenAlertas
    dengue: ResumenDengue
    malaria: ResumenMalaria
    nota: str
