"""Umbrales de alerta configurables (TASK-023, REQ-009, REQ-010).

`obtener_umbral` es el punto de lectura que debe usar
app/ml/evaluacion_alertas.py (TASK-015): consulta la BD en cada llamada, sin
cache, de modo que un cambio hecho con `POST /admin/umbrales` se refleja en la
siguiente evaluacion sin redeploy (criterio de aceptacion de REQ-010).
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Departamento, Enfermedad, UmbralConfiguracion
from app.services.errores import RecursoNoEncontrado

# REFERENCIAL: REQ-009 cita "ej. probabilidad >= 70%" como ejemplo de umbral;
# no hay un valor oficial validado. Se usa solo cuando el admin no configuro
# ninguno para esa enfermedad.
UMBRAL_POR_DEFECTO_PCT = Decimal("70.00")


def _buscar(db: Session, enfermedad_id: int, departamento_id: int | None):
    condicion = (
        UmbralConfiguracion.departamento_id.is_(None)
        if departamento_id is None
        else UmbralConfiguracion.departamento_id == departamento_id
    )
    return db.scalar(
        select(UmbralConfiguracion).where(
            UmbralConfiguracion.enfermedad_id == enfermedad_id, condicion
        )
    )


def obtener_umbral(
    db: Session, enfermedad_id: int, departamento_id: int | None = None
) -> Decimal:
    """Umbral vigente: el del departamento, si no el general de la enfermedad,
    si no UMBRAL_POR_DEFECTO_PCT."""
    if departamento_id is not None:
        especifico = _buscar(db, enfermedad_id, departamento_id)
        if especifico is not None:
            return especifico.umbral_probabilidad_pct
    general = _buscar(db, enfermedad_id, None)
    if general is not None:
        return general.umbral_probabilidad_pct
    return UMBRAL_POR_DEFECTO_PCT


def configurar_umbral(
    db: Session,
    *,
    enfermedad_id: int,
    departamento_id: int | None,
    umbral_probabilidad_pct: float,
) -> tuple[UmbralConfiguracion, Enfermedad, Departamento | None, bool]:
    """Crea o actualiza el umbral de (enfermedad, departamento).

    Devuelve (umbral, enfermedad, departamento, creado).
    """
    enfermedad = db.get(Enfermedad, enfermedad_id)
    if enfermedad is None:
        raise RecursoNoEncontrado(f"No existe la enfermedad {enfermedad_id}.")
    departamento = None
    if departamento_id is not None:
        departamento = db.get(Departamento, departamento_id)
        if departamento is None:
            raise RecursoNoEncontrado(f"No existe el departamento {departamento_id}.")

    valor = Decimal(str(umbral_probabilidad_pct)).quantize(Decimal("0.01"))
    umbral = _buscar(db, enfermedad_id, departamento_id)
    creado = umbral is None
    if creado:
        umbral = UmbralConfiguracion(
            enfermedad_id=enfermedad_id,
            departamento_id=departamento_id,
            umbral_probabilidad_pct=valor,
        )
        db.add(umbral)
    else:
        umbral.umbral_probabilidad_pct = valor
    db.commit()
    db.refresh(umbral)
    return umbral, enfermedad, departamento, creado
