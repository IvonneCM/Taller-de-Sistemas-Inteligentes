"""Nombres de las fuentes epidemiologicas, SIN dependencias pesadas.

Viven aparte de app/etl/conectores/epidemiologia.py porque ese modulo importa
pandas y la imagen `api` del Dockerfile no lo instala: la API necesita estos
textos (p. ej. GET /casos/resumen distingue serie semanal de acumulado) y no
debe arrastrar pandas. tests/test_api_ligera.py lo vigila."""

import re

FUENTE_MINSALUD = "Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13"

# Serie SEMANAL de dengue. Cada boletin N trae las semanas 1..N y corrige las
# anteriores; la fuente guarda de que boletin salio el valor (REQ-015).
_SUFIJO_SEMANAL = " (serie semanal)"
_PATRON_BOLETIN = re.compile(r"N\.º (\d+) \(serie semanal\)$")


def fuente_semanal(numero_boletin: int) -> str:
    """Texto de `fuente` para la serie semanal extraida del boletin N."""
    # `casos_epidemiologicos.fuente` es VARCHAR(100): este texto debe medir <= 100.
    return f"Min. Salud y Deportes de Bolivia, Boletín Epidemiológico N.º {numero_boletin}{_SUFIJO_SEMANAL}"


def es_fuente_semanal(fuente: str | None) -> bool:
    return bool(fuente) and fuente.endswith(_SUFIJO_SEMANAL)


def boletin_de_fuente(fuente: str | None) -> int | None:
    """Numero de boletin de una fuente semanal; None si no es semanal."""
    m = _PATRON_BOLETIN.search(fuente or "")
    return int(m.group(1)) if m else None


# Patron SQL LIKE equivalente a `es_fuente_semanal`.
LIKE_FUENTE_SEMANAL = f"%{_SUFIJO_SEMANAL}"

FUENTE_MINSALUD_SEMANAL = fuente_semanal(13)
