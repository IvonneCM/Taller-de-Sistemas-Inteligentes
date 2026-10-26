"""TASK-025 / REQ-012: recomendaciones de atención, no inventarios."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.roles import ROL_ADMIN, ROL_COORDINADOR
from app.core.database import get_db
from app.models import Usuario
from app.schemas.prevencion import RecursosMunicipio
from app.services.errores import RecursoNoEncontrado
from app.services.prevencion import recursos_municipio
from app.services.reglas_prevencion import alcance_municipal

router = APIRouter(prefix="/municipios", tags=["municipios"])


@router.get("/{municipio_id}/recursos", response_model=RecursosMunicipio)
def recursos_del_municipio(
    municipio_id: int,
    usuario: Usuario = Depends(require_role(ROL_ADMIN, ROL_COORDINADOR)),
    db: Session = Depends(get_db),
):
    try:
        alcance_municipal(usuario.rol.nombre, usuario.municipio_asignado_id, municipio_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    try:
        return recursos_municipio(db, municipio_id)
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
