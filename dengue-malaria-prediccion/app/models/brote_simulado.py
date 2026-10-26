"""Modelo ORM: brotes_simulados (vista). Utilizado como sustituto de brotes_confirmados para TASK-034.

La vista la crea la migracion b8e4f2a6c913: municipio, enfermedad y fecha con al
menos un caso confirmado desde 2026. Es una aproximacion REFERENCIAL, no un brote
confirmado (riesgos M-04 y M-08). Solo lectura.
"""

from sqlalchemy import Column, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class BroteSimulado(Base):
    __tablename__ = "brotes_simulados"
    # Es una vista: alembic/env.py la excluye de la comparacion de autogenerate.
    __table_args__ = {"info": {"es_vista": True}}
    # La vista no tiene PK real; usamos combinación de columnas como PK compuesta.
    municipio_id = Column(Integer, ForeignKey("municipios.id"), primary_key=True)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), primary_key=True)
    fecha_confirmacion = Column(Date, primary_key=True)
    casos_observados = Column(Integer)

    municipio = relationship("Municipio")
    enfermedad = relationship("Enfermedad")
