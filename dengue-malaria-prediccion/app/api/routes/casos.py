"""`GET /casos/resumen` (TASK-047, REQ-008, REQ-014). Cualquier rol autenticado."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Usuario
from app.schemas.casos import CasosZona
from app.services import casos as servicio_casos
from app.services.errores import RecursoNoEncontrado

router = APIRouter(tags=["casos"])


@router.get("/casos/resumen", response_model=list[CasosZona])
def resumen_de_casos(
    enfermedad_id: int | None = Query(None, description="Filtra por enfermedad."),
    _usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Casos observados (no predichos) por zona y enfermedad, con su
    granularidad: dengue es semanal; malaria, un acumulado SE1-13 (ADR-005)."""
    try:
        return servicio_casos.resumen_de_casos(db, enfermedad_id=enfermedad_id)
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
