"""Modelo ORM: brotes_simulados (vista). Utilizado como sustituto de brotes_confirmados para TASK-034.
"""

from sqlalchemy import Column, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class BroteSimulado(Base):
    __tablename__ = "brotes_simulados"
    # La vista no tiene PK real; usamos combinación de columnas como PK compuesta.
    municipio_id = Column(Integer, ForeignKey("municipios.id"), primary_key=True)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), primary_key=True)
    fecha_confirmacion = Column(Date, primary_key=True)
    casos_observados = Column(Integer)

    municipio = relationship("Municipio")
    enfermedad = relationship("Enfermedad")
