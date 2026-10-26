"""Carga de un Boletin Epidemiologico en PDF (REQ-014, REQ-015).

  POST /admin/boletines/vista-previa  lee y verifica el PDF; no guarda nada.
  POST /admin/boletines               lo mismo, y guarda tras la confirmacion.

El cliente envia el MISMO archivo dos veces (vista previa y confirmacion): el
servidor no guarda archivos ni estado entre las dos llamadas.

Solo epidemiologo y admin: son los roles que gestionan datos tecnicos. Un
archivo invalido responde 400 con el motivo; uno demasiado grande, 413.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.roles import ROL_ADMIN, ROL_EPIDEMIOLOGO
from app.core.database import get_db
from app.etl.boletin_pdf import BoletinInvalido, ExtraccionBoletin, extraer_boletin
from app.models import Usuario
from app.schemas.boletines import ResultadoBoletin
from app.services import boletines as servicio_boletines
from app.services.errores import RecursoNoEncontrado

router = APIRouter(prefix="/admin/boletines", tags=["boletines"])

# Un boletin pesa ~1-2 MB; 20 MB deja margen sin aceptar cualquier cosa.
MAX_BYTES = 20 * 1024 * 1024


def _leer(archivo: UploadFile) -> ExtraccionBoletin:
    # Rutas sincronas: FastAPI las corre en un hilo aparte, y leer el PDF es
    # trabajo de CPU que no debe bloquear al resto de las peticiones.
    contenido = archivo.file.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera los 20 MB; un boletín pesa mucho menos.")
    try:
        return extraer_boletin(contenido)
    except BoletinInvalido as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/vista-previa", response_model=ResultadoBoletin)
def vista_previa(
    archivo: UploadFile = File(...),
    _usuario: Usuario = Depends(require_role(ROL_EPIDEMIOLOGO, ROL_ADMIN)),
    db: Session = Depends(get_db),
):
    """Lee el boletin y muestra que se guardaria, sin escribir nada."""
    extraccion = _leer(archivo)
    try:
        return servicio_boletines.planificar(db, extraccion)
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.post("", response_model=ResultadoBoletin)
def cargar(
    archivo: UploadFile = File(...),
    usuario: Usuario = Depends(require_role(ROL_EPIDEMIOLOGO, ROL_ADMIN)),
    db: Session = Depends(get_db),
):
    """Guarda los casos semanales de dengue del boletin (ver la politica en
    app/services/boletines.py). No cambia las predicciones."""
    extraccion = _leer(archivo)
    try:
        return servicio_boletines.aplicar(db, extraccion, usuario_id=usuario.id)
    except RecursoNoEncontrado as error:
        raise HTTPException(status_code=409, detail=str(error))
