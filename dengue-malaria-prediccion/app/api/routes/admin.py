"""`POST /admin/umbrales` (TASK-023, REQ-010). Solo rol admin."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.roles import ROL_ADMIN
from app.core.database import get_db
from app.models import Usuario
from app.schemas.umbrales import UmbralIn, UmbralOut
from app.services import umbrales as servicio_umbrales
from app.services.errores import RecursoNoEncontrado

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/umbrales", response_model=UmbralOut, status_code=201)
def configurar_umbral(
    datos: UmbralIn,
    respuesta: Response,
    _usuario: Usuario = Depends(require_role(ROL_ADMIN)),
    db: Session = Depends(get_db),
):
    """Crea (201) o actualiza (200) el umbral de alerta de una enfermedad,
    general o por departamento. Surte efecto en la siguiente evaluacion de
    alertas, sin redeploy (REQ-010)."""
    try:
        umbral, enfermedad, departamento, creado = servicio_umbrales.configurar_umbral(
            db,
            enfermedad_id=datos.enfermedad_id,
            departamento_id=datos.departamento_id,
            umbral_probabilidad_pct=datos.umbral_probabilidad_pct,
        )
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
    if not creado:
        respuesta.status_code = 200
    return UmbralOut(
        id=umbral.id,
        enfermedad_id=enfermedad.id,
        enfermedad=enfermedad.nombre,
        departamento_id=umbral.departamento_id,
        departamento=departamento.nombre if departamento else None,
        umbral_probabilidad_pct=umbral.umbral_probabilidad_pct,
        creado=creado,
    )
