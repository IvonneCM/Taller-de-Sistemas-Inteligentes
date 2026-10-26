"""Consultas de predicciones vigentes por zona (TASK-019, TASK-020).

"Vigente" = la ultima prediccion generada para cada (municipio, enfermedad),
desempatando por id. Las predicciones son inmutables (NFR-009): esta capa solo
lee; nunca actualiza ni borra.
"""

import json
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased

from app.models import (
    Departamento, Enfermedad, Modelo, Municipio, Prediccion,
)
from app.services.errores import RecursoNoEncontrado

def _vigentes(*, municipio_id: int | None = None, enfermedad_id: int | None = None):
    """Subconsulta con la ultima prediccion por (municipio, enfermedad)."""
    stmt = (
        select(Prediccion)
        .distinct(Prediccion.municipio_id, Prediccion.enfermedad_id)
        .order_by(
            Prediccion.municipio_id,
            Prediccion.enfermedad_id,
            Prediccion.fecha_generacion.desc(),
            Prediccion.id.desc(),
        )
    )
    if municipio_id is not None:
        stmt = stmt.where(Prediccion.municipio_id == municipio_id)
    if enfermedad_id is not None:
        stmt = stmt.where(Prediccion.enfermedad_id == enfermedad_id)
    return aliased(Prediccion, stmt.subquery("vigentes"))


def listar_zonas_riesgo(db: Session, *, enfermedad_id: int | None = None) -> list[dict]:
    """Zonas con su nivel de riesgo vigente y su geometria (REQ-001, REQ-006).

    Una sola consulta, sin N+1, para sostener NFR-004 (< 2 s con 350
    municipios). Orden: riesgo mas alto primero, luego mayor probabilidad.
    """
    vig = _vigentes(enfermedad_id=enfermedad_id)
    centroide = func.ST_Centroid(Municipio.geometria)
    filas = db.execute(
        select(
            vig,
            Municipio.nombre,
            Departamento.id,
            Departamento.nombre,
            Enfermedad.nombre,
            func.ST_AsGeoJSON(Municipio.geometria, 6),
            func.ST_Y(centroide),
            func.ST_X(centroide),
        )
        .join(Municipio, Municipio.id == vig.municipio_id)
        .join(Departamento, Departamento.id == Municipio.departamento_id)
        .join(Enfermedad, Enfermedad.id == vig.enfermedad_id)
        .order_by(
            case(
                (vig.nivel_riesgo == "alto", 0),
                (vig.nivel_riesgo == "medio", 1),
                else_=2,
            ),
            vig.probabilidad_pct.desc(),
            Municipio.nombre,
            Enfermedad.nombre,
        )
    ).all()

    return [
        {
            "municipio_id": p.municipio_id,
            "municipio": municipio,
            "departamento_id": dep_id,
            "departamento": dep_nombre,
            "enfermedad_id": p.enfermedad_id,
            "enfermedad": enfermedad,
            "nivel_riesgo": p.nivel_riesgo,
            "probabilidad_pct": p.probabilidad_pct,
            "nivel_confianza": p.nivel_confianza,
            "fecha_generacion": p.fecha_generacion,
            "fecha_estimada_riesgo": p.fecha_estimada_riesgo,
            "centroide": {"lat": lat, "lon": lon},
            "geometria": json.loads(geojson),
        }
        for p, municipio, dep_id, dep_nombre, enfermedad, geojson, lat, lon in filas
    ]


def obtener_zona(db: Session, municipio_id: int) -> dict:
    """Datos basicos de una zona; RecursoNoEncontrado si no existe."""
    fila = db.execute(
        select(Municipio.id, Municipio.nombre, Departamento.id, Departamento.nombre)
        .join(Departamento, Departamento.id == Municipio.departamento_id)
        .where(Municipio.id == municipio_id)
    ).first()
    if fila is None:
        raise RecursoNoEncontrado(f"No existe el municipio {municipio_id}.")
    return {
        "municipio_id": fila[0],
        "municipio": fila[1],
        "departamento_id": fila[2],
        "departamento": fila[3],
    }


def predicciones_vigentes_de_zona(
    db: Session, municipio_id: int, *, enfermedad_id: int | None = None
) -> list[dict]:
    """Prediccion vigente de la zona por enfermedad, con modelo y variables."""
    vig = _vigentes(municipio_id=municipio_id, enfermedad_id=enfermedad_id)
    filas = db.execute(
        select(vig, Enfermedad.nombre, Modelo.nombre, Modelo.version)
        .join(Enfermedad, Enfermedad.id == vig.enfermedad_id)
        .join(Modelo, Modelo.id == vig.modelo_id)
        .order_by(Enfermedad.nombre)
    ).all()
    return [
        {
            "prediccion_id": p.id,
            "enfermedad_id": p.enfermedad_id,
            "enfermedad": enfermedad,
            "modelo_id": p.modelo_id,
            "modelo_nombre": modelo_nombre,
            "modelo_version": modelo_version,
            "nivel_riesgo": p.nivel_riesgo,
            "probabilidad_pct": p.probabilidad_pct,
            "nivel_confianza": p.nivel_confianza,
            "fecha_generacion": p.fecha_generacion,
            "fecha_estimada_riesgo": p.fecha_estimada_riesgo,
            "variables_explicativas": p.variables_explicativas,
        }
        for p, enfermedad, modelo_nombre, modelo_version in filas
    ]


def validar_enfermedad(db: Session, enfermedad_id: int) -> None:
    if db.get(Enfermedad, enfermedad_id) is None:
        raise RecursoNoEncontrado(f"No existe la enfermedad {enfermedad_id}.")


# Campos que la vista resumida (rol "autoridad" y demas no tecnicos) nunca
# recibe: detalle del modelo y explicabilidad (REQ-007).
CAMPOS_SOLO_TECNICOS = frozenset(
    {
        "prediccion_id", "modelo_id", "modelo_nombre", "modelo_version",
        "variables_explicativas",
    }
)


def a_resumen(prediccion: dict) -> dict:
    return {k: v for k, v in prediccion.items() if k not in CAMPOS_SOLO_TECNICOS}


__all__ = [
    "a_resumen", "listar_zonas_riesgo", "obtener_zona",
    "predicciones_vigentes_de_zona", "validar_enfermedad",
    "CAMPOS_SOLO_TECNICOS",
]
