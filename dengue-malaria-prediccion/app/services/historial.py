"""Historial de predicciones vs. brotes confirmados de una zona (TASK-021,
REQ-008, insumo de NFR-002).

Regla de correlacion (REFERENCIAL, definida aqui por no estar fijada en
requirements.md): una prediccion "acerto" si existe un brote confirmado de la
MISMA enfermedad y zona con `fecha_confirmacion` a no mas de
VENTANA_CORRELACION_DIAS de su `fecha_estimada_riesgo`. Si hay varios, se toma
el mas cercano (en empate, el mas temprano). La ventana de 7 dias equivale a
una semana epidemiologica, la granularidad de los datos del piloto. Es una
comparacion descriptiva, no una metrica validada de precision del modelo.
"""

from datetime import date, timezone

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.models import BroteConfirmado, Enfermedad, Prediccion
from app.services.predicciones import obtener_zona

VENTANA_CORRELACION_DIAS = 7


def _correlacionar(prediccion: Prediccion, brotes: list[BroteConfirmado]):
    candidatos = [
        b for b in brotes
        if b.enfermedad_id == prediccion.enfermedad_id
        and abs((b.fecha_confirmacion - prediccion.fecha_estimada_riesgo).days)
        <= VENTANA_CORRELACION_DIAS
    ]
    if not candidatos:
        return None
    return min(
        candidatos,
        key=lambda b: (
            abs((b.fecha_confirmacion - prediccion.fecha_estimada_riesgo).days),
            b.fecha_confirmacion,
        ),
    )


def historial_de_zona(
    db: Session,
    municipio_id: int,
    *,
    enfermedad_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> dict:
    """Predicciones (cronologicas) y brotes confirmados de la zona.

    `desde`/`hasta` filtran por fecha de generacion de la prediccion (fecha
    UTC) y por fecha de confirmacion del brote. La correlacion usa todos los
    brotes de la zona, para no perder un brote que cae justo fuera del rango.
    """
    zona = obtener_zona(db, municipio_id)

    fecha_gen_utc = cast(func.timezone("UTC", Prediccion.fecha_generacion), Date)
    q_pred = (
        select(Prediccion, Enfermedad.nombre)
        .join(Enfermedad, Enfermedad.id == Prediccion.enfermedad_id)
        .where(Prediccion.municipio_id == municipio_id)
        .order_by(Prediccion.fecha_generacion, Prediccion.id)
    )
    q_brotes = (
        select(BroteConfirmado, Enfermedad.nombre)
        .join(Enfermedad, Enfermedad.id == BroteConfirmado.enfermedad_id)
        .where(BroteConfirmado.municipio_id == municipio_id)
        .order_by(BroteConfirmado.fecha_confirmacion, BroteConfirmado.id)
    )
    if enfermedad_id is not None:
        q_pred = q_pred.where(Prediccion.enfermedad_id == enfermedad_id)
        q_brotes = q_brotes.where(BroteConfirmado.enfermedad_id == enfermedad_id)
    if desde is not None:
        q_pred = q_pred.where(fecha_gen_utc >= desde)
    if hasta is not None:
        q_pred = q_pred.where(fecha_gen_utc <= hasta)

    predicciones = db.execute(q_pred).all()
    brotes = db.execute(q_brotes).all()
    brotes_orm = [b for b, _ in brotes]

    historial = []
    for p, enfermedad in predicciones:
        brote = _correlacionar(p, brotes_orm)
        historial.append(
            {
                "prediccion_id": p.id,
                "enfermedad_id": p.enfermedad_id,
                "enfermedad": enfermedad,
                "fecha_generacion": p.fecha_generacion,
                "fecha_estimada_riesgo": p.fecha_estimada_riesgo,
                "nivel_riesgo": p.nivel_riesgo,
                "probabilidad_pct": p.probabilidad_pct,
                "nivel_confianza": p.nivel_confianza,
                "brote_confirmado": brote is not None,
                "brote_confirmado_id": brote.id if brote else None,
                "fecha_brote_confirmado": brote.fecha_confirmacion if brote else None,
                "anticipacion_dias": (
                    (brote.fecha_confirmacion
                     - p.fecha_generacion.astimezone(timezone.utc).date()).days
                    if brote else None
                ),
            }
        )

    brotes_filtrados = [
        {
            "id": b.id,
            "enfermedad_id": b.enfermedad_id,
            "enfermedad": enfermedad,
            "fecha_confirmacion": b.fecha_confirmacion,
            "fuente": b.fuente,
        }
        for b, enfermedad in brotes
        if (desde is None or b.fecha_confirmacion >= desde)
        and (hasta is None or b.fecha_confirmacion <= hasta)
    ]

    return {
        **zona,
        "desde": desde,
        "hasta": hasta,
        "ventana_correlacion_dias": VENTANA_CORRELACION_DIAS,
        "predicciones": historial,
        "brotes_confirmados": brotes_filtrados,
    }
