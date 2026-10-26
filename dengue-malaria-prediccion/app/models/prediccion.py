"""Modelo ORM: predicciones. Implementa design.md §3 (tabla `predicciones`),
la que consumen TASK-019, TASK-020 y TASK-021 y la que escribira el pipeline
de TASK-014.

Inmutable a nivel de aplicacion (NFR-009, CLAUDE.md regla 4): solo INSERT,
nunca UPDATE. Este modelo no ofrece ningun metodo de actualizacion y los
servicios de la API (app/services) solo la leen.

Los CHECK reflejan REQ-001 (nivel de riesgo), REQ-002 (diferencia de 21 a 28
dias entre generacion y fecha estimada) y REQ-003 (probabilidad 0-100 y
confianza). `fecha_generacion` es timestamptz (misma divergencia ya
documentada para `fecha_ingesta` en design.md §3); el CHECK de la ventana
usa la fecha en UTC para que no dependa de la zona horaria de la sesion.
"""

from sqlalchemy import (
    CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer,
    Numeric, String, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

NIVELES = ("bajo", "medio", "alto")


class Prediccion(Base):
    __tablename__ = "predicciones"
    __table_args__ = (
        CheckConstraint(
            "fecha_estimada_riesgo - CAST(fecha_generacion AT TIME ZONE 'UTC' AS date) "
            "BETWEEN 21 AND 28",
            name="ck_prediccion_horizonte_21_28_dias",
        ),
        CheckConstraint(
            "nivel_riesgo IN ('bajo', 'medio', 'alto')",
            name="ck_prediccion_nivel_riesgo",
        ),
        CheckConstraint(
            "probabilidad_pct >= 0 AND probabilidad_pct <= 100",
            name="ck_prediccion_probabilidad_0_100",
        ),
        CheckConstraint(
            "nivel_confianza IN ('bajo', 'medio', 'alto')",
            name="ck_prediccion_nivel_confianza",
        ),
        CheckConstraint(
            "jsonb_typeof(variables_explicativas) = 'array'",
            name="ck_prediccion_variables_es_lista",
        ),
        # Soporta "prediccion vigente por zona" (ultima por municipio y enfermedad).
        Index(
            "ix_predicciones_municipio_enfermedad_fecha",
            "municipio_id", "enfermedad_id", "fecha_generacion",
        ),
    )

    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), nullable=False)
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)
    fecha_generacion = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fecha_estimada_riesgo = Column(Date, nullable=False)
    nivel_riesgo = Column(String(10), nullable=False)
    probabilidad_pct = Column(Numeric(5, 2), nullable=False)
    nivel_confianza = Column(String(10), nullable=False)
    # Lista ordenada [{"variable": str, "peso": float}, ...] (REQ-004).
    # none_as_null: None se guarda como NULL de SQL (y falla el NOT NULL) en
    # vez de como el valor JSON `null`, que si pasaria el NOT NULL.
    variables_explicativas = Column(JSONB(none_as_null=True), nullable=False)

    municipio = relationship("Municipio")
    enfermedad = relationship("Enfermedad")
    modelo = relationship("Modelo")
