"""`GET /panel/resumen`: indicadores de la pantalla de resumen. Cualquier rol
autenticado (son agregados nacionales, sin detalle tecnico de las predicciones)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Usuario
from app.schemas.panel import PanelResumen
from app.services import panel as servicio_panel

router = APIRouter(tags=["panel"])


@router.get("/panel/resumen", response_model=PanelResumen)
def resumen_del_panel(_usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alertas, riesgo vigente, serie semanal de dengue y municipios con mas
    casos, en una sola llamada. Sin datos cargados devuelve ceros y listas vacias."""
    return servicio_panel.resumen_panel(db)
