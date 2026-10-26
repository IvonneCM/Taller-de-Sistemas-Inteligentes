"""Listado de alertas emitidas (TASK-022, REQ-009).

REQ-005: solo se publican alertas cuya prediccion tiene al menos una variable
explicativa. app/ml/evaluacion_alertas.py (TASK-015) ya impide crear alertas
sin justificacion; este filtro es una segunda barrera por si llegara una fila
incompleta a la tabla (p. ej. una carga manual).
"""

from datetime import date, datetime, timezone

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.orm import Session

from app.models import Alerta, Enfermedad, Municipio, Prediccion
from app.services.predicciones import _vigentes

LIMITE_POR_DEFECTO = 100
LIMITE_MAXIMO = 500


def listar_alertas(
    db: Session,
    *,
    municipio_id: int | None = None,
    enfermedad_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limite: int = LIMITE_POR_DEFECTO,
    desplazamiento: int = 0,
    solo_vigentes: bool = False,
) -> list[dict]:
    """Alertas mas recientes primero, filtradas por zona, enfermedad y fecha
    de emision (fecha UTC)."""
    variables = Prediccion.variables_explicativas
    # CASE evita evaluar jsonb_array_length sobre un valor que no es arreglo.
    n_variables = case(
        (func.jsonb_typeof(variables) == "array", func.jsonb_array_length(variables)),
        else_=0,
    )
    fecha_emision_utc = cast(func.timezone("UTC", Alerta.fecha_emision), Date)

    stmt = (
        select(Alerta, Prediccion, Municipio, Enfermedad.nombre)
        .join(Prediccion, Prediccion.id == Alerta.prediccion_id)
        .join(Municipio, Municipio.id == Prediccion.municipio_id)
        .join(Enfermedad, Enfermedad.id == Prediccion.enfermedad_id)
        .where(n_variables > 0)
        .order_by(Alerta.fecha_emision.desc(), Alerta.id.desc())
        .limit(limite)
        .offset(desplazamiento)
    )
    if municipio_id is not None:
        stmt = stmt.where(Prediccion.municipio_id == municipio_id)
    if enfermedad_id is not None:
        stmt = stmt.where(Prediccion.enfermedad_id == enfermedad_id)
    if desde is not None:
        stmt = stmt.where(fecha_emision_utc >= desde)
    if hasta is not None:
        stmt = stmt.where(fecha_emision_utc <= hasta)
    if solo_vigentes:
        # La selección existente considera TODAS las predicciones, incluidas
        # las que no generaron alerta. No filtrar primero por fecha o alerta.
        vigente = _vigentes()
        variables_validas = func.jsonb_path_query_array(
            variables,
            r'strict $[*] ? (@.type() == "object" && @.variable.type() == "string" '
            r'&& @.variable like_regex "[^[:space:]]" && @.peso.type() == "number")',
            "{}", True,
        )
        stmt = stmt.join(vigente, vigente.id == Prediccion.id).where(
            Prediccion.fecha_estimada_riesgo >= datetime.now(timezone.utc).date(),
            Alerta.justificacion.op("~")("[^[:space:]]"),
            # Todas las variables deben conservar el contrato {variable,peso};
            # lista vacía o elementos mal formados no justifican la alerta.
            func.jsonb_array_length(variables_validas) == n_variables,
        )

    return [
        {
            "id": a.id,
            "prediccion_id": a.prediccion_id,
            "municipio_id": m.id,
            "municipio": m.nombre,
            "departamento_id": m.departamento_id,
            "enfermedad_id": p.enfermedad_id,
            "enfermedad": enfermedad,
            "nivel_riesgo": p.nivel_riesgo,
            "probabilidad_pct": p.probabilidad_pct,
            "umbral_aplicado": a.umbral_aplicado,
            "fecha_emision": a.fecha_emision,
            "fecha_estimada_riesgo": p.fecha_estimada_riesgo,
            "justificacion": a.justificacion,
            "variables_explicativas": p.variables_explicativas,
        }
        for a, p, m, enfermedad in db.execute(stmt).all()
    ]
