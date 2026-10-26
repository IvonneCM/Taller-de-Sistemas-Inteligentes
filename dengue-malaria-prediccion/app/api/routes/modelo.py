"""`GET /modelo/desempeno` (TASK-026, REQ-016). Solo epidemiologo y admin."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.roles import ROL_ADMIN, ROL_EPIDEMIOLOGO
from app.core.database import get_db
from app.models import Usuario
from app.schemas.desempeno import DesempenoModelo
from app.services import desempeno as servicio_desempeno
from app.services.errores import RecursoNoEncontrado

router = APIRouter(prefix="/modelo", tags=["modelo"])


@router.get("/desempeno", response_model=DesempenoModelo)
def desempeno_del_modelo(
    enfermedad_id: int | None = Query(None, description="Filtra por enfermedad."),
    desde: date | None = Query(None, description="Fecha estimada de riesgo desde (YYYY-MM-DD)."),
    hasta: date | None = Query(None, description="Fecha estimada de riesgo hasta (YYYY-MM-DD)."),
    nivel_minimo: Literal["bajo", "medio", "alto"] = Query(
        "medio", description="Nivel desde el que una prediccion cuenta como positiva."),
    _usuario: Usuario = Depends(require_role(ROL_EPIDEMIOLOGO, ROL_ADMIN)),
    db: Session = Depends(get_db),
):
    """Precision espacial, sensibilidad y anticipacion del modelo contra los brotes
    confirmados de un periodo. Sin brotes o sin predicciones, las metricas son
    `null` y `estado` lo explica; nunca se inventa un numero."""
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(status_code=422, detail="`desde` no puede ser posterior a `hasta`.")
    try:
        return servicio_desempeno.calcular_desempeno(
            db, enfermedad_id=enfermedad_id, desde=desde, hasta=hasta, nivel_minimo=nivel_minimo)
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
