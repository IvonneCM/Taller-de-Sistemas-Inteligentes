"""Nombres de las fuentes epidemiologicas, SIN dependencias pesadas.

Viven aparte de app/etl/conectores/epidemiologia.py porque ese modulo importa
pandas y la imagen `api` del Dockerfile no lo instala: la API necesita estos
textos (p. ej. GET /casos/resumen distingue serie semanal de acumulado) y no
debe arrastrar pandas. tests/test_api_ligera.py lo vigila."""

FUENTE_MINSALUD = "Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13"
# `casos_epidemiologicos.fuente` es VARCHAR(100): este texto debe medir <= 100.
FUENTE_MINSALUD_SEMANAL = "Min. Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13 (serie semanal)"
