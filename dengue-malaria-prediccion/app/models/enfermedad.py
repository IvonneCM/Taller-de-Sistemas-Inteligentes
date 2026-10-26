"""Modelo ORM: enfermedades. Implementa TASK-005 / REQ-018."""

from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Enfermedad(Base):
    __tablename__ = "enfermedades"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
