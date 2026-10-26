"""Modelo ORM: brotes_confirmados. Implementa design.md §3 y soporta REQ-008
(TASK-021: historial de predicciones vs. brotes confirmados) y NFR-002.

Divergencia respecto a design.md §3 (anotada ahi tambien): `municipio_id` y
`enfermedad_id` son NOT NULL; un brote sin zona o sin enfermedad no se puede
comparar con ninguna prediccion. Es un dato agregado por municipio y fecha
(REQ-020): sin datos de pacientes.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class BroteConfirmado(Base):
    __tablename__ = "brotes_confirmados"

    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), nullable=False)
    fecha_confirmacion = Column(Date, nullable=False)
    fuente = Column(String(100), nullable=False)

    municipio = relationship("Municipio")
    enfermedad = relationship("Enfermedad")
