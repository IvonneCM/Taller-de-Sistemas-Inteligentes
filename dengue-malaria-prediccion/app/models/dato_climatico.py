"""Modelo ORM: datos_climaticos. Implementa TASK-006 / REQ-013, REQ-015."""

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Numeric,
    UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DatoClimatico(Base):
    __tablename__ = "datos_climaticos"
    __table_args__ = (
        UniqueConstraint("municipio_id", "fecha", name="uq_clima_municipio_fecha"),
    )

    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    temperatura_media_c = Column(Numeric(4, 1), nullable=True)
    humedad_relativa_pct = Column(Numeric(4, 1), nullable=True)
    precipitacion_mm = Column(Numeric(6, 1), nullable=True)
    fuente = Column(String(100), nullable=False)
    fecha_ingesta = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    es_dato_imputado = Column(Boolean, nullable=False, server_default="false")

    municipio = relationship("Municipio", back_populates="datos_climaticos")
