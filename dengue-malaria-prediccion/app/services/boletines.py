"""Carga de un boletin subido por una persona (REQ-014, REQ-015).

Dos pasos, con el MISMO calculo: `planificar` describe que cambiaria sin
escribir (vista previa) y `aplicar` lo guarda tras la confirmacion.

Politica (evita contar dos veces un mismo caso):
  - Cada municipio queda con UNA serie semanal de dengue, la del boletin mas
    reciente que lo trae. Un boletin N trae las semanas 1..N ya corregidas, asi
    que reemplaza los valores de un boletin anterior (fila actualizada, con la
    fuente del boletin nuevo) y agrega las semanas que faltaban.
  - Si el municipio ya tiene datos de un boletin igual o mas reciente, no se
    toca (subir un boletin viejo no deshace correcciones).
  - Municipios fuera del catalogo se informan y se omiten: nunca se crean al
    vuelo (igual que el conector de TASK-009).
  - La tabla de casos no es inmutable (NFR-009 cubre predicciones y alertas);
    cada revision aplicada se devuelve y se registra en el log.

Las predicciones NO cambian al guardar: el modelo lee el panel semanal del
pipeline de datos (casos + clima), que se reconstruye aparte.
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.etl.boletin_pdf import ExtraccionBoletin, normalizar_municipio
from app.etl.fuentes import LIKE_FUENTE_SEMANAL, boletin_de_fuente, fuente_semanal
from app.models import CasoEpidemiologico, Enfermedad, Municipio
from app.services.errores import RecursoNoEncontrado

logger = logging.getLogger("app.boletines")

NOTA = (
    "Los casos guardados se ven en el Resumen y el Mapa. Las predicciones no cambian "
    "todavía: el modelo usa el panel semanal del pipeline de datos (casos + clima), "
    "que se reconstruye aparte."
)


def _fecha_fin_semana(anio: int, semana: int) -> date:
    """Domingo de la semana ISO (misma convencion que app/etl/conectores/epidemiologia.py)."""
    lunes = date.fromisocalendar(anio, semana, 1)
    return date.fromordinal(lunes.toordinal() + 6)


def _calcular(db: Session, ext: ExtraccionBoletin) -> tuple[dict, list]:
    dengue = db.execute(select(Enfermedad).where(Enfermedad.nombre == "dengue")).scalar_one_or_none()
    if dengue is None:
        raise RecursoNoEncontrado("La enfermedad 'dengue' no está en el catálogo.")

    catalogo = {normalizar_municipio(m.nombre): m for m in db.execute(select(Municipio)).scalars()}
    existentes: dict[tuple[int, date], CasoEpidemiologico] = {}
    boletin_actual: dict[int, int] = {}
    for caso in db.execute(
        select(CasoEpidemiologico).where(
            CasoEpidemiologico.enfermedad_id == dengue.id,
            CasoEpidemiologico.fuente.like(LIKE_FUENTE_SEMANAL),
        )
    ).scalars():
        existentes[(caso.municipio_id, caso.fecha_reporte)] = caso
        numero = boletin_de_fuente(caso.fuente) or 0
        boletin_actual[caso.municipio_id] = max(numero, boletin_actual.get(caso.municipio_id, 0))

    fuente = fuente_semanal(ext.semana)
    municipios, fuera, revisiones, operaciones = [], [], [], []
    nuevas = actualizadas = 0
    for fila in ext.municipios:
        m = catalogo.get(fila.clave)
        if m is None:
            fuera.append(fila.nombre)
            continue
        previo = boletin_actual.get(m.id)
        resumen = {"municipio_id": m.id, "municipio": m.nombre, "casos": sum(fila.semanas),
                   "boletin_anterior": previo, "semanas_nuevas": 0, "semanas_revisadas": 0}
        if previo is not None and previo >= ext.semana:
            resumen["accion"] = "omitido"
            municipios.append(resumen)
            continue
        for semana, casos in enumerate(fila.semanas, start=1):
            fecha = _fecha_fin_semana(ext.anio, semana)
            caso = existentes.get((m.id, fecha))
            if caso is None:
                resumen["semanas_nuevas"] += 1
                operaciones.append(("insertar", m.id, fecha, casos, None))
            else:
                if caso.casos_confirmados != casos:
                    resumen["semanas_revisadas"] += 1
                    revisiones.append({"municipio": m.nombre, "semana": semana,
                                       "antes": caso.casos_confirmados, "despues": casos})
                operaciones.append(("actualizar", m.id, fecha, casos, caso))
                actualizadas += 1
        nuevas += resumen["semanas_nuevas"]
        resumen["accion"] = "nuevo" if previo is None else "actualiza"
        municipios.append(resumen)

    plan = {
        "semana": ext.semana, "anio": ext.anio, "pagina": ext.pagina, "fuente": fuente,
        "total_casos": ext.total, "totales_semana": ext.totales_semana,
        "municipios_en_boletin": len(ext.municipios),
        "municipios": municipios, "fuera_de_catalogo": sorted(fuera),
        "filas_nuevas": nuevas, "filas_actualizadas": actualizadas, "revisiones": revisiones,
        "verificacion": "Las filas y columnas coinciden con los totales impresos en el boletín.",
        "nota": NOTA,
    }
    return plan, [(op, mid, fecha, casos, caso, dengue.id, fuente) for op, mid, fecha, casos, caso in operaciones]


def planificar(db: Session, ext: ExtraccionBoletin) -> dict:
    """Vista previa: que cambiaria, sin escribir nada."""
    plan, _ = _calcular(db, ext)
    return {**plan, "guardado": False}


def aplicar(db: Session, ext: ExtraccionBoletin, *, usuario_id: int) -> dict:
    """Guarda el boletin segun la politica del modulo y confirma la transaccion."""
    plan, operaciones = _calcular(db, ext)
    ahora = datetime.now(timezone.utc)
    for op, municipio_id, fecha, casos, caso, enfermedad_id, fuente in operaciones:
        if op == "insertar":
            db.add(CasoEpidemiologico(
                municipio_id=municipio_id, enfermedad_id=enfermedad_id, fecha_reporte=fecha,
                casos_confirmados=casos, fuente=fuente, es_dato_imputado=False,
            ))
        else:
            caso.casos_confirmados = casos
            caso.fuente = fuente
            caso.fecha_ingesta = ahora
    db.commit()
    logger.info(
        "Boletin SE %s/%s cargado por el usuario %s: %s filas nuevas, %s actualizadas, %s revisiones %s",
        ext.semana, ext.anio, usuario_id, plan["filas_nuevas"], plan["filas_actualizadas"],
        len(plan["revisiones"]), plan["revisiones"],
    )
    return {**plan, "guardado": True}
