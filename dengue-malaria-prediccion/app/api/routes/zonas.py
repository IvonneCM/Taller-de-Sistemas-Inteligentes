"""Endpoints de zonas: mapa de riesgo, prediccion por zona e historial
(TASK-019, TASK-020, TASK-021). Ver design.md §4 y docs/contrato_api.md.

`{id}` es el id del municipio (la zona geografica base, design.md §3).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    ROL_ADMIN, ROL_EPIDEMIOLOGO, UsuarioActual, get_usuario_actual, require_role,
)
from app.core.database import get_db
from app.schemas.zonas import (
    HistorialZona, ZonaPrediccionDetalle, ZonaPrediccionResumen, ZonaRiesgo,
)
from app.services import historial as servicio_historial
from app.services import predicciones as servicio_predicciones
from app.services.errores import RecursoNoEncontrado

router = APIRouter(prefix="/zonas", tags=["zonas"])


def _no_encontrado(error: RecursoNoEncontrado) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.get("/riesgo", response_model=list[ZonaRiesgo])
def zonas_riesgo(
    enfermedad_id: int | None = Query(
        None, description="Filtra por enfermedad; sin filtro devuelve todas."
    ),
    _usuario: UsuarioActual = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """TASK-019 (REQ-001, REQ-006): riesgo vigente de cada zona con geometria,
    para el mapa de calor. Cualquier rol autenticado."""
    if enfermedad_id is not None:
        try:
            servicio_predicciones.validar_enfermedad(db, enfermedad_id)
        except RecursoNoEncontrado as error:
            raise _no_encontrado(error)
    return servicio_predicciones.listar_zonas_riesgo(db, enfermedad_id=enfermedad_id)


@router.get(
    "/{municipio_id}/prediccion",
    response_model=ZonaPrediccionDetalle | ZonaPrediccionResumen,
)
def prediccion_de_zona(
    municipio_id: int,
    enfermedad_id: int | None = Query(None, description="Filtra por enfermedad."),
    usuario: UsuarioActual = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """TASK-020 (REQ-002, REQ-003, REQ-004, REQ-007): prediccion vigente de la
    zona. Epidemiologo y admin reciben la vista completa (variables
    explicativas y modelo); el resto, la resumida. El filtrado ocurre aqui, en
    el servidor, no en el frontend."""
    try:
        zona = servicio_predicciones.obtener_zona(db, municipio_id)
        if enfermedad_id is not None:
            servicio_predicciones.validar_enfermedad(db, enfermedad_id)
    except RecursoNoEncontrado as error:
        raise _no_encontrado(error)

    predicciones = servicio_predicciones.predicciones_vigentes_de_zona(
        db, municipio_id, enfermedad_id=enfermedad_id
    )
    if not predicciones:
        raise HTTPException(
            status_code=404, detail="La zona aun no tiene predicciones vigentes."
        )

    if usuario.ve_detalle_completo:
        return ZonaPrediccionDetalle(**zona, predicciones=predicciones)
    return ZonaPrediccionResumen(
        **zona,
        predicciones=[servicio_predicciones.a_resumen(p) for p in predicciones],
    )


@router.get("/{municipio_id}/historial", response_model=HistorialZona)
def historial_de_zona(
    municipio_id: int,
    enfermedad_id: int | None = Query(None, description="Filtra por enfermedad."),
    desde: date | None = Query(None, description="Fecha minima (YYYY-MM-DD)."),
    hasta: date | None = Query(None, description="Fecha maxima (YYYY-MM-DD)."),
    _usuario: UsuarioActual = Depends(require_role(ROL_EPIDEMIOLOGO, ROL_ADMIN)),
    db: Session = Depends(get_db),
):
    """TASK-021 (REQ-008): predicciones pasadas y brotes confirmados de la
    zona, correlacionados por fecha. Solo epidemiologo y admin."""
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status_code=422, detail="`desde` no puede ser posterior a `hasta`.")
    try:
        if enfermedad_id is not None:
            servicio_predicciones.validar_enfermedad(db, enfermedad_id)
        return servicio_historial.historial_de_zona(
            db, municipio_id, enfermedad_id=enfermedad_id, desde=desde, hasta=hasta
        )
    except RecursoNoEncontrado as error:
        raise _no_encontrado(error)
