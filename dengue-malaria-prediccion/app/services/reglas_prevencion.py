"""Reglas del MVP para TASK-024/025 (REQ-011/012), sin inferencia ni inventarios."""

from app.api.roles import ROL_COORDINADOR

NOTA_MVP = (
    "Los umbrales de riesgo y las recomendaciones son decisiones provisionales "
    "del MVP. No constituyen protocolos oficiales de SEDES ni sustituyen la "
    "evaluación epidemiológica."
)

_RECOMENDACIONES = {
    "alto": ("PRIORITARIO", (
        "Reforzar vigilancia epidemiológica.",
        "Evaluar disponibilidad de insumos.",
        "Priorizar campañas preventivas.",
        "Fortalecer seguimiento de posibles casos.",
    )),
    "medio": ("PREVENTIVO", (
        "Intensificar seguimiento epidemiológico.",
        "Revisar disponibilidad de recursos.",
        "Fortalecer actividades preventivas.",
        "Mantener seguimiento periódico.",
    )),
    "bajo": ("RUTINARIO", (
        "Mantener vigilancia epidemiológica habitual.",
        "Continuar actividades preventivas.",
        "Realizar seguimiento periódico.",
    )),
}


def alcance_municipal(rol: str, asignado: int | None, solicitado: int | None = None):
    """Limita al coordinador antes de consultar datos; RBAC valida los roles."""
    if rol != ROL_COORDINADOR:
        return None
    if asignado is None or (solicitado is not None and solicitado != asignado):
        raise PermissionError("No autorizado para este municipio.")
    return asignado


def priorizar(predicciones: list[dict]) -> list[dict]:
    """Ordena niveles ya calculados por TASK-014; no vuelve a clasificarlos."""
    orden = {"alto": 0, "medio": 1, "bajo": 2}
    filas = sorted(predicciones, key=lambda p: (
        orden[p["nivel_riesgo"]], p["fecha_estimada_riesgo"],
        -p["probabilidad_pct"], p["municipio_id"],
    ))
    return [dict(p, posicion=i) for i, p in enumerate(filas, 1)]


def recomendar(nivel_riesgo: str) -> dict:
    """Recomendación orientativa; un nivel desconocido nunca se trata como bajo."""
    nivel, acciones = _RECOMENDACIONES[nivel_riesgo]
    return {
        "nivel_atencion": nivel,
        "recomendaciones": list(acciones),
        "nota": NOTA_MVP,
    }
