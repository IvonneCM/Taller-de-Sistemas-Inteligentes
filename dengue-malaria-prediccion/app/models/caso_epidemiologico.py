"""Modelo ORM: casos_epidemiologicos. Implementa TASK-006 / REQ-013,
REQ-015.

Nota de granularidad (actualizada 2026-10-25, decision 2 del reparto): el
esquema admite cualquier granularidad; `fecha_reporte` es el DOMINGO de la
semana ISO para filas semanales (dengue: serie real por municipio) y el
cierre del periodo para filas acumuladas (malaria: solo hay acumulados SE1-k).
Las filas semanales y acumuladas de una misma enfermedad no deben mezclarse:
se distinguen por `fuente`. Ver app/etl/conectores/epidemiologia.py.
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
