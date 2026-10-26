"""TASK-024 / REQ-011: priorización de campañas de dengue t+3."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.roles import ROL_COORDINADOR, ROL_SEDES
from app.core.database import get_db
from app.models import Usuario
from app.schemas.prevencion import PrioridadCampana
from app.services.prevencion import listar_priorizacion
from app.services.reglas_prevencion import alcance_municipal

router = APIRouter(prefix="/campanas", tags=["campanas"])


@router.get("/priorizacion", response_model=list[PrioridadCampana])
def priorizacion_campanas(
    usuario: Usuario = Depends(require_role(ROL_SEDES, ROL_COORDINADOR)),
    db: Session = Depends(get_db),
):
    try:
        municipio_id = alcance_municipal(usuario.rol.nombre, usuario.municipio_asignado_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return listar_priorizacion(db, municipio_id=municipio_id)
