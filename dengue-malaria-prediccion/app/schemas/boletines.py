"""Respuesta de la carga de boletines (`POST /admin/boletines[/vista-previa]`)."""

from typing import Literal

from pydantic import BaseModel


class MunicipioBoletin(BaseModel):
    municipio_id: int
    municipio: str
    casos: int
    accion: Literal["nuevo", "actualiza", "omitido"]
    boletin_anterior: int | None
    semanas_nuevas: int
    semanas_revisadas: int


class Revision(BaseModel):
    municipio: str
    semana: int
    antes: int
    despues: int


class ResultadoBoletin(BaseModel):
    guardado: bool
    semana: int
    anio: int
    pagina: int
    fuente: str
    total_casos: int
    totales_semana: list[int]
    municipios_en_boletin: int
    municipios: list[MunicipioBoletin]
    fuera_de_catalogo: list[str]
    filas_nuevas: int
    filas_actualizadas: int
    revisiones: list[Revision]
    verificacion: str
    nota: str
