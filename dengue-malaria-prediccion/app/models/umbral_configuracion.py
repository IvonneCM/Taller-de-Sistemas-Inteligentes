"""Modelo ORM: umbrales_configuracion. Implementa design.md §3 y soporta
REQ-010 (TASK-023: `POST /admin/umbrales`).

Divergencias respecto a design.md §3 (anotadas ahi tambien):
- `enfermedad_id` es NOT NULL: un umbral siempre es "por enfermedad".
- Hay un UNIQUE(enfermedad_id, departamento_id) con NULLS NOT DISTINCT
  (PostgreSQL 15+; el proyecto usa 16) para que exista a lo sumo un umbral
  general (departamento_id NULL) y uno por departamento para cada enfermedad,
  y asi el POST pueda crear-o-actualizar sin duplicar.
- CHECK 0-100 sobre `umbral_probabilidad_pct`.
"""

from sqlalchemy import (
    CheckConstraint, Column, ForeignKey, Integer, Numeric, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UmbralConfiguracion(Base):
    __tablename__ = "umbrales_configuracion"
    __table_args__ = (
        CheckConstraint(
            "umbral_probabilidad_pct >= 0 AND umbral_probabilidad_pct <= 100",
            name="ck_umbral_0_100",
        ),
        UniqueConstraint(
            "enfermedad_id", "departamento_id",
            name="uq_umbral_enfermedad_departamento",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    enfermedad_id = Column(Integer, ForeignKey("enfermedades.id"), nullable=False)
    # NULL = aplica a todos los departamentos.
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=True)
    umbral_probabilidad_pct = Column(Numeric(5, 2), nullable=False)

    enfermedad = relationship("Enfermedad")
    departamento = relationship("Departamento")
