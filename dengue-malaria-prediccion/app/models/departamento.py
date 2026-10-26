"""Modelo ORM: departamentos. Implementa TASK-005 / REQ-017."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)

    municipios = relationship("Municipio", back_populates="departamento")
