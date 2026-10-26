"""Esquemas de TASK-023 (`POST /admin/umbrales`, REQ-010)."""

from pydantic import BaseModel, ConfigDict, Field


class UmbralIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enfermedad_id: int
    # None = el umbral aplica a todos los departamentos.
    departamento_id: int | None = None
    umbral_probabilidad_pct: float = Field(ge=0, le=100)


class UmbralOut(BaseModel):
    id: int
    enfermedad_id: int
    enfermedad: str
    departamento_id: int | None
    departamento: str | None
    umbral_probabilidad_pct: float
    creado: bool
