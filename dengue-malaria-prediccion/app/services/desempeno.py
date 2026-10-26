"""Desempeno del modelo sobre un periodo (TASK-026, REQ-016; insumo de NFR-001 y
NFR-002).

Definiciones (provisionales del MVP; requirements.md no las fija):
- Una prediccion es POSITIVA si su nivel de riesgo es `nivel_minimo` o mayor
  (por defecto, medio o alto).
- Un brote confirmado "corresponde" a una prediccion si es de la MISMA zona y
  enfermedad y su fecha de confirmacion queda a no mas de
  VENTANA_CORRELACION_DIAS de la fecha estimada de riesgo (la misma regla del
  historial). Si hay varios, se toma el mas cercano.
- precision espacial = aciertos / predicciones positivas: de las zonas que el
  modelo marco en riesgo, cuantas tuvieron un brote confirmado.
- sensibilidad = brotes detectados / brotes confirmados del periodo: de los
  brotes, cuantos habia marcado el modelo.
- anticipacion = dias entre la generacion de la prediccion y la confirmacion del
  brote, solo para los aciertos. Con horizonte >= 21 dias y ventana +-7, un
  acierto nunca anticipa menos de 14 dias (objetivo de NFR-002): lo que importa
  validar es si los aciertos existen, no su margen.

Con cero predicciones o cero brotes confirmados las metricas son None, no 0: no
se fabrica un resultado donde no hay datos (CLAUDE.md regla 1).
"""

from datetime import date
from statistics import mean, median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BroteConfirmado, BroteSimulado, Prediccion
from app.services.errores import RecursoNoEncontrado
from app.services.historial import VENTANA_CORRELACION_DIAS
from app.services.predicciones import validar_enfermedad

ORDEN = {"bajo": 0, "medio": 1, "alto": 2}
# Objetivos de diseno (requirements.md NFR-001 y NFR-002), NO resultados validados.
OBJETIVO_PRECISION_PCT = 75.0
OBJETIVO_ANTICIPACION_DIAS = 14

NOTA = (
    "Resultados sobre los datos del piloto, no garantias generales. Los objetivos de "
    "NFR-001 y NFR-002 son cifras de diseno que todavia no se pueden validar: la "
    "cantidad de brotes confirmados disponible es muy pequena o nula."
)


def _porcentaje(parte: int, total: int) -> float | None:
    return round(100 * parte / total, 1) if total else None


def calcular_desempeno(
    db: Session,
    *,
    enfermedad_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    nivel_minimo: str = "medio",
    usar_brotes_simulados: bool = False,
) -> dict:
    if enfermedad_id is not None:
        validar_enfermedad(db, enfermedad_id)
    if nivel_minimo not in ORDEN:
        raise RecursoNoEncontrado(f"Nivel de riesgo desconocido: {nivel_minimo}.")

    q_pred = select(Prediccion)
    q_brotes = select(BroteSimulado) if usar_brotes_simulados else select(BroteConfirmado)
    if enfermedad_id is not None:
        q_pred = q_pred.where(Prediccion.enfermedad_id == enfermedad_id)
        q_brotes = q_brotes.where(BroteConfirmado.enfermedad_id == enfermedad_id)
    if desde is not None:
        q_pred = q_pred.where(Prediccion.fecha_estimada_riesgo >= desde)
        q_brotes = q_brotes.where((BroteSimulado.fecha_confirmacion if usar_brotes_simulados else BroteConfirmado.fecha_confirmacion) >= desde)
    if hasta is not None:
        q_pred = q_pred.where(Prediccion.fecha_estimada_riesgo <= hasta)
        q_brotes = q_brotes.where((BroteSimulado.fecha_confirmacion if usar_brotes_simulados else BroteConfirmado.fecha_confirmacion) <= hasta)

    predicciones = db.execute(q_pred).scalars().all()
    brotes = db.execute(q_brotes).scalars().all()
    # Para corresponder una prediccion con un brote no se recorta al periodo: un
    # brote confirmado justo despues de `hasta` sigue siendo el de esa prediccion.
    todos_los_brotes = brotes
    if desde is not None or hasta is not None:
        q_todos = select(BroteConfirmado)
        if enfermedad_id is not None:
            q_todos = q_todos.where(BroteConfirmado.enfermedad_id == enfermedad_id)
        todos_los_brotes = db.execute(q_todos).scalars().all()

    por_zona: dict[tuple[int, int], list[BroteConfirmado]] = {}
    for b in todos_los_brotes:
        por_zona.setdefault((b.municipio_id, b.enfermedad_id), []).append(b)

    def brote_cercano(p: Prediccion):
        candidatos = [
            b for b in por_zona.get((p.municipio_id, p.enfermedad_id), [])
            if abs((b.fecha_confirmacion - p.fecha_estimada_riesgo).days) <= VENTANA_CORRELACION_DIAS
        ]
        return min(candidatos, key=lambda b: (abs((b.fecha_confirmacion - p.fecha_estimada_riesgo).days),
                                              b.fecha_confirmacion), default=None)

    positivas = [p for p in predicciones if ORDEN[p.nivel_riesgo] >= ORDEN[nivel_minimo]]
    aciertos, anticipaciones = [], []
    for p in positivas:
        brote = brote_cercano(p)
        if brote is not None:
            aciertos.append(p)
            anticipaciones.append((brote.fecha_confirmacion - p.fecha_generacion.date()).days)

    detectados = 0
    for b in brotes:
        if any(
            p.municipio_id == b.municipio_id and p.enfermedad_id == b.enfermedad_id
            and abs((b.fecha_confirmacion - p.fecha_estimada_riesgo).days) <= VENTANA_CORRELACION_DIAS
            for p in positivas
        ):
            detectados += 1

    if not predicciones:
        estado = "sin_predicciones"
    elif not brotes:
        estado = "sin_brotes_confirmados"
    else:
        estado = "calculado"

    return {
        "desde": desde, "hasta": hasta, "enfermedad_id": enfermedad_id, "nivel_minimo": nivel_minimo,
        "ventana_correlacion_dias": VENTANA_CORRELACION_DIAS,
        "predicciones_evaluadas": len(predicciones),
        "predicciones_positivas": len(positivas),
        "aciertos": len(aciertos),
        "falsas_alarmas": len(positivas) - len(aciertos),
        "brotes_confirmados": len(brotes),
        "brotes_detectados": detectados,
        # Sin brotes no hay forma de saber si una alarma fue falsa: no se calcula.
        "precision_espacial_pct": _porcentaje(len(aciertos), len(positivas)) if brotes and positivas else None,
        "sensibilidad_pct": _porcentaje(detectados, len(brotes)),
        "anticipacion_dias_media": round(mean(anticipaciones), 1) if anticipaciones else None,
        "anticipacion_dias_mediana": float(median(anticipaciones)) if anticipaciones else None,
        "aciertos_con_anticipacion_minima": sum(d >= OBJETIVO_ANTICIPACION_DIAS for d in anticipaciones),
        "objetivos": {
            "precision_espacial_pct": OBJETIVO_PRECISION_PCT,
            "anticipacion_dias": OBJETIVO_ANTICIPACION_DIAS,
            "nota": "Objetivos de diseno (NFR-001, NFR-002), no resultados validados.",
        },
        "estado": estado,
        "nota": NOTA,
    }
