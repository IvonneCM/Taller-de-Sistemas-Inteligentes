"""Modelo ORM: roles. Implementa TASK-007 / REQ-019.

Roles previstos por design.md §3: autoridad, sedes, epidemiologo,
coordinador_municipal, admin.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)

    usuarios = relationship("Usuario", back_populates="rol")
