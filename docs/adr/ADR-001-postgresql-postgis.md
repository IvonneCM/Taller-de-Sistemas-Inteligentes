# ADR-001: PostgreSQL 16 + PostGIS como base de datos

- **Estado:** Aceptado
- **Fecha:** 2026-09-16
- **Decisores:** Equipo SIPTB
- **Relacionado:** `design.md` §1 y §3, REQ-001, REQ-011, REQ-015, NFR-009

## Contexto

El sistema debe almacenar datos epidemiológicos agregados por municipio y
semana, datos climáticos, predicciones inmutables y alertas, y a la vez
responder consultas **geoespaciales** (zonas, municipios, mapas de calor por
departamento/municipio). Además, REQ-015 exige registrar la procedencia
(`fuente`) y `fecha_ingesta` de cada dato, y NFR-009 exige auditabilidad de las
predicciones.

## Alternativas consideradas

1. **PostgreSQL sin PostGIS** — base relacional sin soporte geoespacial nativo.
2. **MySQL / MariaDB** — relacional maduro, pero sin geometrías/consultas
   espaciales comparables.
3. **SQLite** — simple para prototipo, pero no apto para despliegue
   multiusuario concurrente.
4. **MongoDB + índices geoespaciales** — flexible, pero menor integridad
   referencial y peor ajuste para datos tabulares auditables.
5. **Archivos GIS + procesamiento con GeoPandas** — suficiente para análisis
   puntual, pero no como fuente de verdad para una API multiusuario.

## Decisión

Usar **PostgreSQL 16 con la extensión PostGIS** como base de datos única para
el sistema.

## Justificación

- PostGIS es el estándar de facto para datos geoespaciales y cubre los mapas de
  calor y consultas por zona/municipio/departamento que pide REQ-001/REQ-011.
- El modelo relacional garantiza integridad referencial y trazabilidad
  (`fuente`, `fecha_ingesta`, inserción inmutable de predicciones) exigidas por
  REQ-015 y NFR-009.
- PostgreSQL es soportado de forma nativa por la plataforma de despliegue
  elegida (ver ADR-003) y por Alembic para migraciones.
- Permite el mismo motor para datos tabulares y espaciales, evitando
  sincronizar dos almacenes.

## Consecuencias

- **Positivas:** una sola fuente de verdad; consultas geoespaciales eficientes;
  escalabilidad y madurez del ecosistema.
- **Negativas / costos:** requiere una instancia con PostGIS habilitado (extensiones),
  mayor complejidad en migraciones y en pruebas locales (contenedor con PostGIS).
- **Requisito operativo:** la instancia de despliegue debe permitir crear la
  extensión PostGIS; si no, se debe reevaluar (ver ADR-003).
