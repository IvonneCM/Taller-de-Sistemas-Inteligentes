"""Modelo ORM: casos_epidemiologicos. Implementa TASK-006 / REQ-013,
REQ-015.

Nota de granularidad (decision corregida 2026-10-25, ver CONTEXT.md): la
fuente real (Min. de Salud y Deportes, Boletin Epidemiologico N.13) entrega
acumulados municipales SE1-13, no series semana-a-semana. `fecha_reporte`
puede entonces representar el fin del periodo acumulado reportado (no un dia
puntual con conteo diario). El modelo no fuerza una granularidad porque el
esquema es compatible con cualquiera (acumulado por periodo hoy, semanal si
en el futuro la fuente lo permite) — ver REQ-014 en tasks.md TASK-009.
"""

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean, ForeignKey,
    CheckConstraint, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CasoEpidemiologico(Base):
    __tablename__ = "casos_epidemiologicos"
    __table_args__ = (
        CheckConstraint("casos_confirmados >= 0", name="ck_casos_no_negativos"),
        UniqueConstraint(
            "municipio_id", "enfermedad_id", "fecha_reporte", "fuente",
            name="uq_caso_municipio_enfermedad_fecha_fuente",
        ),
    )

    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), nullable=False)
    fecha_reporte = Column(Date, nullable=False)
    casos_confirmados = Column(Integer, nullable=False)
    fuente = Column(String(100), nullable=False)
    fecha_ingesta = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    es_dato_imputado = Column(Boolean, nullable=False, server_default="false")

    municipio = relationship("Municipio", back_populates="casos_epidemiologicos")
    enfermedad = relationship("Enfermedad")
