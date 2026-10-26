"""Lectura de dengue t+3 elegible para TASK-024/025, sin alterar TASK-019/020."""

from datetime import date, datetime, timezone

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session, aliased

from app.models import Departamento, Enfermedad, Modelo, Municipio, Prediccion
from app.services.errores import RecursoNoEncontrado
from app.services.predicciones import obtener_zona
from app.services.reglas_prevencion import priorizar, recomendar


def fecha_actual_utc() -> date:
    return datetime.now(timezone.utc).date()


def consulta_elegibles(hoy: date, municipio_id: int | None = None):
    """Filtra ANTES de DISTINCT ON; fecha de hoy incluida, sin casts de JSON.

    JSONB @> rechaza horizon textual, booleano o ausente sin errores de cast.
    El modelo y la predicción deben pertenecer a la misma enfermedad dengue.
    """
    elegibles = (
        select(Prediccion)
        .join(Modelo, Modelo.id == Prediccion.modelo_id)
        .join(Enfermedad, Enfermedad.id == Prediccion.enfermedad_id)
        .where(
            Enfermedad.nombre == "dengue",
            Modelo.enfermedad_id == Prediccion.enfermedad_id,
            func.jsonb_typeof(Modelo.metricas_entrenamiento) == "object",
            Modelo.metricas_entrenamiento.contains({
                "enfermedad": "dengue", "horizonte_semanas": 3,
            }),
            Prediccion.fecha_estimada_riesgo == (
                cast(func.timezone("UTC", Prediccion.fecha_generacion), Date) + 21
            ),
            Prediccion.fecha_estimada_riesgo >= hoy,
        )
    )
    if municipio_id is not None:
        elegibles = elegibles.where(Prediccion.municipio_id == municipio_id)
    elegibles = elegibles.distinct(Prediccion.municipio_id).order_by(
        Prediccion.municipio_id,
        Prediccion.fecha_generacion.desc(), Prediccion.id.desc(),
    )
    vigente = aliased(Prediccion, elegibles.subquery("dengue_t3_vigente"))
    return (
        select(
            vigente.id.label("prediccion_id"),
            Municipio.id.label("municipio_id"),
            Municipio.nombre.label("municipio"),
            Departamento.id.label("departamento_id"),
            Departamento.nombre.label("departamento"),
            vigente.enfermedad_id,
            vigente.probabilidad_pct, vigente.nivel_riesgo,
            vigente.nivel_confianza, vigente.fecha_generacion,
            vigente.fecha_estimada_riesgo,
        )
        .select_from(vigente)
        .join(Municipio, Municipio.id == vigente.municipio_id)
        .join(Departamento, Departamento.id == Municipio.departamento_id)
    )


def predicciones_elegibles(db: Session, *, municipio_id: int | None = None) -> list[dict]:
    filas = db.execute(consulta_elegibles(fecha_actual_utc(), municipio_id)).mappings()
    return [dict(fila, enfermedad="dengue", horizonte_semanas=3) for fila in filas]


def listar_priorizacion(db: Session, *, municipio_id: int | None = None) -> list[dict]:
    return priorizar(predicciones_elegibles(db, municipio_id=municipio_id))


def recursos_municipio(db: Session, municipio_id: int) -> dict:
    obtener_zona(db, municipio_id)  # Distingue municipio inexistente de falta de predicción.
    filas = predicciones_elegibles(db, municipio_id=municipio_id)
    if not filas:
        raise RecursoNoEncontrado(
            "El municipio no tiene predicción vigente elegible de dengue a t+3."
        )
    fila = filas[0]
    return dict(fila, **recomendar(fila["nivel_riesgo"]))
