"""Evaluacion de alertas tempranas de brotes (TASK-015).

Implementa REQ-005, REQ-009 y REQ-010:
- REQ-009: Emite alerta cuando una zona supera el umbral configurable.
- REQ-005: Prohibido generar alertas de riesgo sin justificacion explicita
  basada en las variables del modelo. Si no existen variables explicativas,
  la alerta NO se publica y se registra como advertencia en el log.
- REQ-010: Utiliza los umbrales configurados por el administrador
  mediante `app.services.umbrales.obtener_umbral` (por departamento o por
  enfermedad, sin cache en memoria).
"""

from __future__ import annotations

import argparse
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alerta, Municipio, Prediccion
from app.services.umbrales import obtener_umbral

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)


def construir_justificacion(
    variables_explicativas: Sequence[dict[str, Any]],
    *,
    probabilidad_pct: float | Decimal | None = None,
    umbral: float | Decimal | None = None,
    max_variables: int = 3,
) -> str:
    """Construye una justificacion textual clara y descriptiva (REQ-005).

    Exige al menos una variable explicativa con nombre valido; rechaza
    listas vacias para garantizar que ninguna alerta quede huerfana.
    """
    if not variables_explicativas:
        raise ValueError(
            "No se puede construir una justificacion sin variables explicativas (REQ-005)."
        )

    factores: list[str] = []
    for item in variables_explicativas[:max_variables]:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("variable", "")).strip()
        if not nombre:
            continue
        peso = item.get("peso")
        if peso is not None:
            try:
                peso_val = float(peso)
                factores.append(f"{nombre} (peso: {peso_val:.2f})")
            except (ValueError, TypeError):
                factores.append(nombre)
        else:
            factores.append(nombre)

    if not factores:
        raise ValueError(
            "Ninguna variable explicativa valida encontrada en la lista (REQ-005)."
        )

    detalle = ", ".join(factores)
    if probabilidad_pct is not None and umbral is not None:
        prob_float = float(probabilidad_pct)
        umbral_float = float(umbral)
        return (
            f"Probabilidad de brote del {prob_float:.1f}% supera el umbral "
            f"configurado ({umbral_float:.1f}%). Factores determinantes: {detalle}."
        )
    return f"Factores explicativos determinantes del modelo: {detalle}."


def evaluar_prediccion(
    db: Session,
    prediccion: Prediccion,
    *,
    fecha_emision: datetime | None = None,
    forzar_reemision: bool = False,
) -> Alerta | None:
    """Evalua una prediccion individual contra el umbral vigente.

    Reglas de negocio:
    1. Si `probabilidad_pct < umbral`, no corresponde alerta.
    2. Si `probabilidad_pct >= umbral` pero no tiene variables explicativas,
       REQ-005 prohibe crear la alerta; se registra en log y retorna None.
    3. Si ya existe una alerta para esta prediccion y no se fuerza, se
       retorna la existente sin duplicar.
    4. Si cumple los requisitos, crea la fila en `alertas` y la agrega a la sesion.
    """
    departamento_id: int | None = None
    if prediccion.municipio is not None:
        departamento_id = prediccion.municipio.departamento_id
    elif prediccion.municipio_id is not None:
        muni = db.get(Municipio, prediccion.municipio_id)
        if muni is not None:
            departamento_id = muni.departamento_id

    umbral = obtener_umbral(
        db,
        enfermedad_id=prediccion.enfermedad_id,
        departamento_id=departamento_id,
    )

    prob = Decimal(str(prediccion.probabilidad_pct))
    if prob < umbral:
        return None

    # REQ-005: Validar presencia de explicabilidad antes de generar alerta
    variables = prediccion.variables_explicativas
    if not variables or not isinstance(variables, Sequence) or len(variables) == 0:
        logger.warning(
            "Alerta omitida para prediccion %s: probabilidad %s%% supera umbral %s%% "
            "pero no existen variables explicativas del modelo (REQ-005).",
            prediccion.id,
            prob,
            umbral,
        )
        return None

    # Evitar duplicados si ya fue emitida
    alerta_existente = db.scalar(
        select(Alerta).where(Alerta.prediccion_id == prediccion.id)
    )
    if alerta_existente is not None and not forzar_reemision:
        return alerta_existente

    justificacion = construir_justificacion(
        variables,
        probabilidad_pct=prob,
        umbral=umbral,
    )

    alerta = Alerta(
        prediccion_id=prediccion.id,
        umbral_aplicado=umbral,
        justificacion=justificacion,
        **({"fecha_emision": fecha_emision} if fecha_emision else {}),
    )
    db.add(alerta)
    db.flush()
    return alerta


def evaluar_alertas_lote(
    db: Session,
    predicciones: Sequence[Prediccion | int],
    *,
    fecha_emision: datetime | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    """Evalua un conjunto de predicciones y genera las alertas aplicables.

    `predicciones` puede ser una lista de instancias `Prediccion` o de `id`s.
    Devuelve un diccionario resumen con las metricas del lote.
    """
    alertas_creadas: list[int] = []
    omitidas_sin_explicacion: list[int] = []
    no_superan: int = 0
    ya_existentes: int = 0

    for item in predicciones:
        if isinstance(item, int):
            pred = db.get(Prediccion, item)
            if pred is None:
                continue
        else:
            pred = item

        # Comprobar si ya tenia alerta antes de evaluar
        tenia_alerta = db.scalar(
            select(Alerta.id).where(Alerta.prediccion_id == pred.id)
        ) is not None

        alerta = evaluar_prediccion(db, pred, fecha_emision=fecha_emision)

        if alerta is None:
            # Determinar por que fue None
            departamento_id = (
                pred.municipio.departamento_id
                if pred.municipio
                else None
            )
            umbral = obtener_umbral(
                db,
                enfermedad_id=pred.enfermedad_id,
                departamento_id=departamento_id,
            )
            if Decimal(str(pred.probabilidad_pct)) >= umbral:
                omitidas_sin_explicacion.append(pred.id)
            else:
                no_superan += 1
        elif tenia_alerta:
            ya_existentes += 1
        else:
            alertas_creadas.append(alerta.id)

    if commit:
        db.commit()

    return {
        "alertas_creadas": alertas_creadas,
        "total_creadas": len(alertas_creadas),
        "omitidas_sin_explicacion": omitidas_sin_explicacion,
        "no_superan_umbral": no_superan,
        "ya_existentes": ya_existentes,
    }


def evaluar_alertas_pendientes(
    db: Session,
    *,
    limite: int | None = 200,
) -> dict[str, Any]:
    """Busca predicciones recientes sin alerta asociada y las evalua."""
    stmt = (
        select(Prediccion)
        .outerjoin(Alerta, Alerta.prediccion_id == Prediccion.id)
        .where(Alerta.id.is_(None))
        .order_by(Prediccion.fecha_generacion.desc())
    )
    if limite is not None:
        stmt = stmt.limit(limite)

    pendientes = list(db.scalars(stmt).all())
    return evaluar_alertas_lote(db, pendientes, commit=True)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI para evaluar alertas sobre la base de datos."""
    parser = argparse.ArgumentParser(
        description="Evalua alertas para predicciones existentes (TASK-015)."
    )
    parser.add_argument(
        "--prediccion-id",
        type=int,
        default=None,
        help="Evalua una prediccion especifica por su ID.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=200,
        help="Limite de predicciones pendientes a evaluar (por defecto: 200).",
    )
    args = parser.parse_args(argv)

    from app.core.database import SessionLocal

    with SessionLocal() as db:
        if args.prediccion_id is not None:
            pred = db.get(Prediccion, args.prediccion_id)
            if pred is None:
                print(f"Error: Prediccion {args.prediccion_id} no encontrada.")
                return 1
            alerta = evaluar_prediccion(db, pred)
            db.commit()
            if alerta:
                print(f"Alerta creada: id={alerta.id}, justificacion='{alerta.justificacion}'")
            else:
                print(f"No se creo alerta para la prediccion {args.prediccion_id}.")
            return 0

        resumen = evaluar_alertas_pendientes(db, limite=args.limite)
        print("Resumen de evaluacion de alertas:")
        print(f"  Alertas creadas: {resumen['total_creadas']}")
        print(f"  Omitidas sin explicacion (REQ-005): {len(resumen['omitidas_sin_explicacion'])}")
        print(f"  No superan umbral: {resumen['no_superan_umbral']}")
        print(f"  Ya existentes: {resumen['ya_existentes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
