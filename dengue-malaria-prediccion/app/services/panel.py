"""Indicadores para la pantalla de resumen (`GET /panel/resumen`).

Reutiliza lo que ya existe en vez de duplicar reglas:
  - alertas vigentes: `listar_alertas(solo_vigentes=True)` (TASK-022);
  - prediccion vigente por zona: `_vigentes()` (TASK-019);
  - casos: dengue semanal y malaria acumulado, sin mezclarlos (ADR-005).
Sin datos cargados devuelve ceros y listas vacias, nunca cifras inventadas."""

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.etl.fuentes import LIKE_FUENTE_SEMANAL
from app.models import Alerta, CasoEpidemiologico, Departamento, Enfermedad, Municipio
from app.services.alertas import LIMITE_MAXIMO, listar_alertas
from app.services.predicciones import _vigentes

TOP = 5
NOTA = (
    "Los casos son observados (Boletin Epidemiologico); el riesgo es la prediccion vigente "
    "del modelo baseline, entrenado con pocas semanas: no es una garantia. La ultima semana "
    "de casos es provisional y suele corregirse al alza."
)


def _semana(fecha: date, casos: int) -> dict:
    return {"fecha": fecha, "semana": fecha.isocalendar().week, "casos": int(casos)}


def _top_municipios(db: Session, enfermedad: str, *, semanal: bool) -> tuple[list[dict], int]:
    """(top de municipios por casos, total de municipios con casos)."""
    condicion = (
        CasoEpidemiologico.fuente.like(LIKE_FUENTE_SEMANAL)
        if semanal else CasoEpidemiologico.fuente.not_like(LIKE_FUENTE_SEMANAL)
    )
    filas = db.execute(
        select(Municipio.id, Municipio.nombre, Departamento.nombre,
               func.sum(CasoEpidemiologico.casos_confirmados))
        .join(Municipio, Municipio.id == CasoEpidemiologico.municipio_id)
        .join(Departamento, Departamento.id == Municipio.departamento_id)
        .join(Enfermedad, Enfermedad.id == CasoEpidemiologico.enfermedad_id)
        .where(Enfermedad.nombre == enfermedad, condicion)
        .group_by(Municipio.id, Municipio.nombre, Departamento.nombre)
        .order_by(func.sum(CasoEpidemiologico.casos_confirmados).desc(), Municipio.nombre)
    ).all()
    top = [
        {"municipio_id": mid, "municipio": nombre, "departamento": dep, "casos": int(total)}
        for mid, nombre, dep, total in filas[:TOP]
    ]
    return top, len(filas)


def resumen_panel(db: Session) -> dict:
    # --- alertas ---
    emitidas = db.execute(select(func.count(Alerta.id))).scalar_one()
    vigentes = len(listar_alertas(db, solo_vigentes=True, limite=LIMITE_MAXIMO))

    # --- dengue: serie semanal nacional (suma de los municipios cargados) ---
    serie = [
        _semana(fecha, total)
        for fecha, total in db.execute(
            select(CasoEpidemiologico.fecha_reporte, func.sum(CasoEpidemiologico.casos_confirmados))
            .join(Enfermedad, Enfermedad.id == CasoEpidemiologico.enfermedad_id)
            .where(Enfermedad.nombre == "dengue", CasoEpidemiologico.fuente.like(LIKE_FUENTE_SEMANAL))
            .group_by(CasoEpidemiologico.fecha_reporte)
            .order_by(CasoEpidemiologico.fecha_reporte)
        ).all()
    ]
    top_dengue, n_dengue = _top_municipios(db, "dengue", semanal=True)

    # --- dengue: riesgo vigente por municipio ---
    vig = _vigentes()
    enfermedad_dengue = db.execute(select(Enfermedad.id).where(Enfermedad.nombre == "dengue")).scalar_one_or_none()
    predicciones = []
    if enfermedad_dengue is not None:
        predicciones = db.execute(
            select(vig, Municipio.nombre, Departamento.nombre)
            .join(Municipio, Municipio.id == vig.municipio_id)
            .join(Departamento, Departamento.id == Municipio.departamento_id)
            .where(vig.enfermedad_id == enfermedad_dengue)
            .order_by(vig.probabilidad_pct.desc(), Municipio.nombre)
        ).all()
    niveles = {"alto": 0, "medio": 0, "bajo": 0}
    for fila in predicciones:
        niveles[fila[0].nivel_riesgo] = niveles.get(fila[0].nivel_riesgo, 0) + 1
    mayores = [
        {
            "municipio_id": p.municipio_id, "municipio": municipio, "departamento": departamento,
            "nivel_riesgo": p.nivel_riesgo, "probabilidad_pct": float(p.probabilidad_pct),
            "fecha_estimada_riesgo": p.fecha_estimada_riesgo,
        }
        for p, municipio, departamento in predicciones[:TOP]
    ]
    mayor = mayores[0] if mayores else None
    fecha_prediccion = max((f[0].fecha_generacion for f in predicciones), default=None)

    # --- malaria: acumulado, nunca serie semanal ---
    top_malaria, n_malaria = _top_municipios(db, "malaria", semanal=False)
    total_malaria, corte_malaria = db.execute(
        select(func.coalesce(func.sum(CasoEpidemiologico.casos_confirmados), 0),
               func.max(CasoEpidemiologico.fecha_reporte))
        .join(Enfermedad, Enfermedad.id == CasoEpidemiologico.enfermedad_id)
        .where(Enfermedad.nombre == "malaria", CasoEpidemiologico.fuente.not_like(LIKE_FUENTE_SEMANAL))
    ).one()

    return {
        "generado": datetime.now(timezone.utc),
        "alertas": {"emitidas": int(emitidas), "vigentes": vigentes},
        "dengue": {
            "municipios_con_casos": n_dengue,
            "total_casos": sum(s["casos"] for s in serie),
            "serie_semanal": serie,
            "ultima_semana": serie[-1] if serie else None,
            "semana_previa": serie[-2] if len(serie) > 1 else None,
            "top_municipios": top_dengue,
            "riesgo": {**niveles, "total": sum(niveles.values())},
            "mayor_riesgo": mayor,
            "mayores_riesgos": mayores,
            "fecha_prediccion": fecha_prediccion,
        },
        "malaria": {
            "municipios_con_casos": n_malaria,
            "total_casos": int(total_malaria),
            "fecha_corte": corte_malaria,
            "top_municipios": top_malaria,
        },
        "nota": NOTA,
    }
