"""Modelo ORM: municipios (zona geografica base). Implementa TASK-005 /
REQ-017, REQ-018. Columna `geometria` en PostGIS (soporta REQ-006, mapa de
calor)."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class Municipio(Base):
    __tablename__ = "municipios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    departamento_id = Column(
        Integer, ForeignKey("departamentos.id"), nullable=False
    )
    geometria = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    poblacion_estimada = Column(Integer, nullable=True)

    departamento = relationship("Departamento", back_populates="municipios")
    casos_epidemiologicos = relationship(
        "CasoEpidemiologico", back_populates="municipio"
    )
    datos_climaticos = relationship("DatoClimatico", back_populates="municipio")
