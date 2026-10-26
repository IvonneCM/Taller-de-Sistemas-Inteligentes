"""Casos observados por zona y enfermedad (TASK-047, REQ-008, REQ-014).

Una fila por (municipio, enfermedad). Si la enfermedad tiene serie semanal se
usa solo esa; si no, el acumulado. Nunca se suman filas semanales con
acumuladas de la misma enfermedad (duplicaria los casos; ver
docs/contrato_esquema_bd.md)."""

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.etl.fuentes import FUENTE_MINSALUD_SEMANAL
from app.models import CasoEpidemiologico, Departamento, Enfermedad, Municipio
from app.services.predicciones import validar_enfermedad


def resumen_de_casos(db: Session, *, enfermedad_id: int | None = None) -> list[dict]:
    if enfermedad_id is not None:
        validar_enfermedad(db, enfermedad_id)

    centroide = func.ST_Centroid(Municipio.geometria)
    stmt = (
        select(
            Municipio.id, Municipio.nombre, Departamento.id, Departamento.nombre,
            Enfermedad.id, Enfermedad.nombre, CasoEpidemiologico.fuente,
            func.sum(CasoEpidemiologico.casos_confirmados),
            func.min(CasoEpidemiologico.fecha_reporte),
            func.max(CasoEpidemiologico.fecha_reporte),
            func.count(CasoEpidemiologico.id),
            func.ST_AsGeoJSON(Municipio.geometria, 6),
            func.ST_Y(centroide), func.ST_X(centroide),
        )
        .join(Municipio, Municipio.id == CasoEpidemiologico.municipio_id)
        .join(Departamento, Departamento.id == Municipio.departamento_id)
        .join(Enfermedad, Enfermedad.id == CasoEpidemiologico.enfermedad_id)
        .group_by(
            Municipio.id, Municipio.nombre, Departamento.id, Departamento.nombre,
            Enfermedad.id, Enfermedad.nombre, CasoEpidemiologico.fuente, Municipio.geometria,
        )
    )
    if enfermedad_id is not None:
        stmt = stmt.where(CasoEpidemiologico.enfermedad_id == enfermedad_id)

    elegidas: dict[tuple[int, int], dict] = {}
    for (mid, mnombre, did, dnombre, eid, enombre, fuente, total, desde, hasta,
         registros, geojson, lat, lon) in db.execute(stmt).all():
        semanal = fuente == FUENTE_MINSALUD_SEMANAL
        fila = {
            "municipio_id": mid, "municipio": mnombre,
            "departamento_id": did, "departamento": dnombre,
            "enfermedad_id": eid, "enfermedad": enombre,
            "granularidad": "semanal" if semanal else "acumulado",
            "total_casos": int(total), "desde": desde, "hasta": hasta,
            "registros": registros, "fuente": fuente,
            "centroide": {"lat": lat, "lon": lon},
            "geometria": json.loads(geojson),
        }
        previa = elegidas.get((mid, eid))
        if previa is None or (semanal and previa["granularidad"] == "acumulado"):
            elegidas[(mid, eid)] = fila

    return sorted(
        elegidas.values(),
        key=lambda f: (-f["total_casos"], f["municipio"], f["enfermedad"]),
    )
