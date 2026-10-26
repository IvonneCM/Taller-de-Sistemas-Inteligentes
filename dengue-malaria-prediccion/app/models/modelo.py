"""Modelo ORM: modelos entrenados. Implementa TASK-012 / design.md §3.

Guarda una version del modelo y sus metricas de validacion en JSONB. La tabla
`predicciones` de TASK-014 referencia `modelos.id` mediante `modelo_id`, por
lo que esta tabla debe existir antes de persistir predicciones.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Modelo(Base):
    __tablename__ = "modelos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), nullable=True)
    fecha_entrenamiento = Column(DateTime(timezone=True), nullable=False)
    metricas_entrenamiento = Column(JSONB, nullable=True)

    enfermedad = relationship("Enfermedad")
