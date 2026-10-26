"""Modelo ORM: predicciones. Implementa TASK-014 / REQ-001, REQ-002, REQ-003.

La tabla es inmutable a nivel de aplicacion: solo se insertan filas, nunca se
actualizan (NFR-009). Los limites de `nivel_riesgo`, `probabilidad_pct`,
`nivel_confianza` y del horizonte de 21 a 28 dias replican design.md §3.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Prediccion(Base):
    __tablename__ = "predicciones"
    __table_args__ = (
        CheckConstraint(
            "probabilidad_pct >= 0 AND probabilidad_pct <= 100",
            name="ck_prediccion_probabilidad_0_100",
        ),
        CheckConstraint(
            "nivel_riesgo IN ('bajo', 'medio', 'alto')",
            name="ck_prediccion_nivel_riesgo",
        ),
        CheckConstraint(
            "nivel_confianza IN ('bajo', 'medio', 'alto')",
            name="ck_prediccion_nivel_confianza",
        ),
        CheckConstraint(
            "fecha_estimada_riesgo BETWEEN "
            "((fecha_generacion AT TIME ZONE 'UTC')::date + 21) AND "
            "((fecha_generacion AT TIME ZONE 'UTC')::date + 28)",
            name="ck_prediccion_horizonte_21_28_dias",
        ),
    )

    id = Column(Integer, primary_key=True)
    municipio_id = Column(
        Integer, ForeignKey("municipios.id"), nullable=False
    )
    enfermedad_id = Column(
        Integer, ForeignKey("enfermedades.id"), nullable=False
    )
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)
    fecha_generacion = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fecha_estimada_riesgo = Column(Date, nullable=False)
    nivel_riesgo = Column(String(10), nullable=False)
    probabilidad_pct = Column(Numeric(5, 2), nullable=False)
    nivel_confianza = Column(String(10), nullable=False)
    variables_explicativas = Column(JSONB, nullable=False)

    municipio = relationship("Municipio")
    enfermedad = relationship("Enfermedad")
    modelo = relationship("Modelo")
