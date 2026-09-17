# Diagramas C4 — Arquitectura

**Responsable:** Tania Perez
**Sección del backlog:** Architecture

- [`c4-contexto.svg`](./c4-contexto.svg): Nivel 1 (Contexto). Muestra el sistema
  como una caja frente a sus tres usuarios (Autoridad de Salud/SEDES, Médico
  Epidemiólogo, Coordinador Sanitario Municipal) y la única dependencia
  externa: las fuentes de datos públicas.
- [`c4-contenedores.svg`](./c4-contenedores.svg): Nivel 2 (Contenedores). Abre
  el sistema en sus cinco piezas técnicas: Dashboard Web, API REST, Módulo
  ETL/Ingesta, Motor de Predicción y la base PostgreSQL+PostGIS.

## Coherencia con `design.md`

Los contenedores y sus responsabilidades siguen exactamente la arquitectura
ya decidida en [`../../dengue-malaria-prediccion/design.md`](../../dengue-malaria-prediccion/design.md):

| Contenedor del diagrama | Referencia en design.md |
|---|---|
| Dashboard Web (React + Leaflet/Mapbox) | §1, fila "Frontend / Dashboard" |
| API REST (FastAPI) | §1, fila "Backend"; §2, capa "API REST" |
| Módulo ETL / Ingesta | §2, capa "CAPA DE INGESTA (ETL)" |
| Motor de Predicción (batch semanal) | §1, fila "ML"; decisión de ejecución batch semanal |
| PostgreSQL + PostGIS | §1, fila "Base de datos"; §3, modelo de datos |

## Decisiones que quedan explícitas en el propio diagrama

- El Módulo ETL es el único punto que escribe "datos limpios" a la base —
  refleja que la limpieza/imputación (`docs/reglas_calidad_datos.md`,
  implementada en `docs/pipeline_datos.md`) ocurre antes de persistir, no
  dentro de la API.
- El Motor de Predicción se marca explícitamente como **batch semanal**, no
  tiempo real, consistente con la decisión de diseño registrada en
  `design.md` y con el horizonte de predicción de 3-4 semanas del proyecto.
- "Fuentes de Datos Públicas" se modela como sistema externo fuera de
  nuestro control, con la fuente exacta remitida a `design.md` §10 —
  actualmente resuelta en la práctica por `docs/eda_inicial.md`
  (SENAMHI + Ministerio de Salud y Deportes), pendiente de reflejar
  formalmente en `design.md`.

## Qué no cubre todavía este nivel

Los diagramas C4 se detienen en el Nivel 2 (Contenedores). El Nivel 3
(Componentes) y los ADR de las decisiones de stack (PostgreSQL+PostGIS,
FastAPI, Railway) son responsabilidad de Ivonne (`docs/adr/`), no de este
entregable.
