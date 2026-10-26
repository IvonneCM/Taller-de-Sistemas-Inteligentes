"""Modelo ORM: alertas. Implementa design.md §3 (tabla `alertas`).

REQ-005 / CLAUDE.md regla 3: no existe alerta sin justificacion. La columna
`justificacion` es NOT NULL y el CHECK rechaza cadenas vacias o de solo
espacios; la regla de "ademas debe haber al menos una variable explicativa"
la aplica app/ml/evaluacion_alertas.py (TASK-015) antes de insertar.

Inmutable a nivel de aplicacion (NFR-009): solo INSERT.
"""

from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, Text, func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alerta(Base):
    __tablename__ = "alertas"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(justificacion)) > 0",
            name="ck_alerta_justificacion_no_vacia",
        ),
        CheckConstraint(
            "umbral_aplicado >= 0 AND umbral_aplicado <= 100",
            name="ck_alerta_umbral_0_100",
        ),
    )

    id = Column(Integer, primary_key=True)
    prediccion_id = Column(Integer, ForeignKey("predicciones.id"), nullable=False)
    umbral_aplicado = Column(Numeric(5, 2), nullable=False)
    fecha_emision = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    justificacion = Column(Text, nullable=False)

    prediccion = relationship("Prediccion")
