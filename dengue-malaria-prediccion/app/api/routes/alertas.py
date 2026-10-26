"""`GET /alertas` (TASK-022, REQ-009). Cualquier rol autenticado."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Usuario
from app.schemas.alertas import AlertaOut
from app.services import alertas as servicio_alertas

router = APIRouter(tags=["alertas"])


@router.get("/alertas", response_model=list[AlertaOut])
def listar_alertas(
    municipio_id: int | None = Query(None, description="Zona (municipio)."),
    enfermedad_id: int | None = Query(None),
    desde: date | None = Query(None, description="Emision desde (YYYY-MM-DD)."),
    hasta: date | None = Query(None, description="Emision hasta (YYYY-MM-DD)."),
    limite: int = Query(
        servicio_alertas.LIMITE_POR_DEFECTO, ge=1, le=servicio_alertas.LIMITE_MAXIMO
    ),
    desplazamiento: int = Query(0, ge=0),
    _usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alertas emitidas, las mas recientes primero. Cada una incluye su
    justificacion y sus variables explicativas (REQ-005)."""
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status_code=422, detail="`desde` no puede ser posterior a `hasta`.")
    return servicio_alertas.listar_alertas(
        db,
        municipio_id=municipio_id,
        enfermedad_id=enfermedad_id,
        desde=desde,
        hasta=hasta,
        limite=limite,
        desplazamiento=desplazamiento,
    )
