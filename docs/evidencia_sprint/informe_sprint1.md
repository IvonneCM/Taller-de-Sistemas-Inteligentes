# Evidencia de ejecución Scrum — Sprint 1

**Tarea origen:** [Preparar evidencia de Sprint 1: backlog y trabajo realizado](https://app.clickup.com/t/86e39cz27) (ClickUp, lista Discovery)
**Responsable:** Ignacio Retamozo Torrez
**Fecha:** 2026-09-17
**Rama base:** `main` (sincronizada con `origin/main`, commit `5440800`)

Este documento consolida la evidencia de ejecución Scrum del Sprint 1 según los
tres criterios de aceptación de la tarea que lo origina:

1. El Product Goal vigente está enlazado y accesible.
2. El backlog del sprint está organizado por lista en ClickUp con criterios de
   aceptación en cada tarea.
3. Existe evidencia verificable del trabajo (commits, documentos, capturas)
   por cada tarea completada.

Los criterios de aceptacion en las tablas posteriores son un resumen guia de lo que esta presente en Github, por lo cual ahi se encontrara todos los criterios completos.

---

## 1. Product Goal vigente

- **Documento:** [docs/product_goal.md](../product_goal.md)
- **Enunciado:** sistema que predice dónde habrá brotes de dengue/malaria 3-4
  semanas antes, para autoridades de salud pública y equipos de prevención en
  SEDES.
- **Métricas de éxito:** precisión espacial ≥75% (NFR-001) y anticipación
  mínima de 2 semanas (NFR-002), ambas definidas en
  [`dengue-malaria-prediccion/requirements.md`](../../dengue-malaria-prediccion/requirements.md).
- Accesible y versionado en el repositorio desde el Sprint 0 (tarea ClickUp
  [`Redactar Product Goal...`](https://app.clickup.com/t/86e2x3j24)).

## 2. Backlog priorizado en ClickUp

El backlog del Sprint 1 está organizado en el espacio **"Taller de Sistemas
Inteligentes"** de ClickUp, dividido en 5 listas ("carriles"): **Discovery**,
**Data**, **Architecture**, **Build / QA / Deploy** y **Risk**. Las 17 tareas
de este sprint tienen prioridad `high`, el campo `Sprint = 1` y un campo de
texto **"Criterio de aceptación"** con los criterios verificables de cada
entregable (ver detalle por tarea en las secciones 4-8).

**Nota sobre limitaciones de ClickUp:** el campo dedicado **"Enlace a
evidencia"** (tipo URL) del workspace no pudo mantenerse poblado de forma
consistente por restricciones del plan/integración de ClickUp con GitHub —
solo 3 de las 17 tareas lo tienen resuelto directamente en la descripción de
la tarea. Por eso, para el resto, este informe enlaza directamente el
archivo o commit correspondiente en el repositorio como evidencia
verificable, en lugar de depender del campo de ClickUp.

## 3. Resumen del estado (verificado contra el repositorio, no solo ClickUp)

| Carril | Tareas | Completadas (repo) | Observaciones |
|---|---|---|---|
| Discovery | 6 | 6 done  | ver §4 |
| Data | 4 | 4 | ver §5 |
| Architecture | 2 | 2 | ver §6 |
| Build / QA / Deploy | 3 | 3 | ver §7 |
| Risk | 2 | 2 | ver §8 |

---

## 4. Carril: Discovery

| Tarea | Responsable | Estado ClickUp | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| [Preparar cierre: backlog pendiente, bloqueos y próximos pasos](https://app.clickup.com/t/86e39cz8y) | Tania Perez | done | Backlog pendiente listado, bloqueos documentados, viabilidad evaluada, contenido listo para la sección de cierre | [`docs/cierre_sprint1.md`](../cierre_sprint1.md) |
| [Actualizar README del repositorio con estado actual y guía de reproducción](https://app.clickup.com/t/86e39cywv) | Dilan Obed Mamani Pamuri | done | README con estructura clara, guía de reproducción, enlaces a requirements/design/tasks | [`dengue-malaria-prediccion/README.md`](../../dengue-malaria-prediccion/README.md) — versión inicial en commit [`98a4126`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/98a4126) (Dilan), con actualizaciones posteriores de Ivonne, Tania e Ignacio a medida que avanzó el sprint |
| [Redactar declaración de uso de IA y evidencia de revisión humana](https://app.clickup.com/t/86e39cyq0) | Adriana Rocha Vedia | done | Herramientas de IA listadas por tipo de tarea, proceso de revisión humana documentado | [`docs/declaracion_uso_ia.md`](../declaracion_uso_ia.md) — commit [`ba1374d`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/ba1374d) |
| [Documentar alcance y exclusiones del proyecto](https://app.clickup.com/t/86e39cyha) | Ivonne Colque | done | Revisar/complementar "Fuera de alcance" de requirements.md; resumen corto de qué incluye/excluye |  commit [`9255b82`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/9255b82) [`dengue-malaria-prediccion/requirements.md`](../../dengue-malaria-prediccion/requirements.md) |
| [Documentar métricas de valor y criterios de éxito](https://app.clickup.com/t/86e39cybq) | Tania Perez | done | Métricas de valor (NFR-001/002), cómo se miden, distinción entrega actual vs. sistema final | [`docs/metricas_valor.md`](../metricas_valor.md) |
| [Preparar evidencia de Sprint 1: backlog y trabajo realizado](https://app.clickup.com/t/86e39cz27) (esta tarea) | Ignacio Retamozo Torrez | in development → **completada con este documento** | Product Goal enlazado, backlog organizado por lista con criterios, evidencia verificable por tarea | Este mismo documento: [`docs/evidencia_sprint1/informe_sprint1.md`](informe_sprint1.md) |

## 5. Carril: Data

| Tarea | Responsable | Estado ClickUp | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| [Documentar restricciones de privacidad y licencias de los datos](https://app.clickup.com/t/86e39d03m) | Ignacio Retamozo Torrez | done | Cumplimiento de REQ-020 confirmado; licencias de cada fuente pública documentadas | [`docs/privacidad_datos.md`](../privacidad_datos.md) — commit [`5702920`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/5702920) "Analisis de Privacidad" |
| [Definir reglas de calidad, limpieza e imputación de datos](https://app.clickup.com/t/86e39czxj) | Dilan Obed Mamani Pamuri | done | Reglas de limpieza/imputación para datos climáticos y epidemiológicos, casos de datos faltantes cubiertos | [`docs/reglas_calidad_datos.md`](../reglas_calidad_datos.md) — commit [`fbd2512`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/fbd2512) |
| [Análisis exploratorio de datos (EDA) inicial](https://app.clickup.com/t/86e39czr0) | Adriana Rocha Vedia | done | Estadísticas básicas del dataset, resultado reproducible subido al repo | [`docs/eda_inicial.md`](../eda_inicial.md) + [`scripts/eda_inicial.py`](../../scripts/eda_inicial.py), [`eda_climatico.py`](../../scripts/eda_climatico.py), [`eda_integrado.py`](../../scripts/eda_integrado.py) y sus carpetas de salida (`scripts/eda_output/`, `eda_climatico_output/`, `eda_integrado_output/`) |
| [Inventario de fuentes de datos epidemiológicos y climáticos](https://app.clickup.com/t/86e39czh3) | Ivonne Colque | done | Cada fuente candidata listada con forma de acceso; estado confirmado/abierto indicado | [`docs/inventario_datos.md`](../inventario_datos.md) — commit [`bcc4c1d`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/bcc4c1d), actualizado en [`797d0d5`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/797d0d5). También adjunta captura en la tarea de ClickUp |

## 6. Carril: Architecture

| Tarea | Responsable | Estado ClickUp | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| [Crear registro de decisiones de arquitectura (ADR)](https://app.clickup.com/t/86e39d0c3) | Ivonne Colque | done | Mínimo 3 ADR con contexto, alternativas, decisión y justificación | [`docs/adr/`](../adr/): [ADR-001](../adr/ADR-001-postgresql-postgis.md) (PostgreSQL+PostGIS), [ADR-002](../adr/ADR-002-python-fastapi.md) (FastAPI), [ADR-003](../adr/ADR-003-despliegue-railway.md) (Railway), [ADR-004](../adr/ADR-004-linea-base-nacional-referencia-inicial.md) (línea base nacional) |
| [Elaborar diagramas C4 de la arquitectura (Contexto y Contenedores)](https://app.clickup.com/t/86e39d088) | Tania Perez | done | Diagrama de Contexto y de Contenedores, coherentes con design.md | [`docs/c4/`](../c4/): [`c4-contexto.svg`](../c4/c4-contexto.svg), [`c4-contenedores.svg`](../c4/c4-contenedores.svg), [`README.md`](../c4/README.md) |

## 7. Carril: Build / QA / Deploy

| Tarea | Responsable | Estado ClickUp | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| [Preparar entorno y datos iniciales (Línea Base — Paso 1)](https://app.clickup.com/t/86e39d0w2) | Ignacio Retamozo Torrez | done | Entorno reproducible confirmado, estado inicial de datos descrito, evidencia de arranque correcto | [`docs/entorno_datos_iniciales.md`](../entorno_datos_iniciales.md) + 31 logs de ejecución en [`docs/evidencia_entorno/`](../evidencia_entorno/) (versión de Python, creación de venv, `dvc pull`, arranque de `uvicorn`, `pytest`, etc.) — commit [`18dde9e`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/18dde9e) |
| [Construir pipeline reproducible de datos (Línea Base — Paso 2)](https://app.clickup.com/t/86e39d10v) | Tania Perez | done | Scripts de ingesta/limpieza ejecutables end-to-end, ejecución documentada, evidencia reproducible (no solo captura) | [`docs/pipeline_datos.md`](../pipeline_datos.md) + [`scripts/limpieza_datos.py`](../../scripts/limpieza_datos.py) — commit [`6325da0`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/6325da0) |
| [Establecer línea base y registrar resultados/experimentos (Línea Base — Paso 3)](https://app.clickup.com/t/86e39d192) | Ivonne Colque | done | Línea base documentada, experimentos registrados (incluidos fallidos), documento subido al repo | [`docs/linea_base.md`](../linea_base.md) (commit [`9d8d154`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/9d8d154)) + [`docs/resultados_linea_base.md`](../resultados_linea_base.md) y [`scripts/linea_base_modelo.py`](../../scripts/linea_base_modelo.py) con salidas en `scripts/linea_base_output/` (commits [`6909bb6`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/6909bb6), [`365031e`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/365031e)) |

## 8. Carril: Risk

| Tarea | Responsable | Estado ClickUp | Criterio de aceptación | Evidencia |
|---|---|---|---|---|
| [Definir controles de seguridad desde el diseño](https://app.clickup.com/t/86e39d0pc) | Dilan Obed Mamani Pamuri | done | Controles vigentes listados (JWT, RBAC, no PII, HTTPS), vinculados a requisitos (NFR-005, REQ-019, REQ-020) | [`docs/controles_seguridad.md`](../controles_seguridad.md) — commit [`50c12f8`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/50c12f8) |
| [Elaborar Risk Register inicial (riesgos técnicos, de datos y de IA)](https://app.clickup.com/t/86e39d0hq) | Adriana Rocha Vedia | done | Tabla de riesgos con categoría/probabilidad/impacto/mitigación; al menos un riesgo por categoría | [`docs/risk_register.md`](../risk_register.md) — commit [`83704d6`](https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes/commit/83704d6) |

---

## 9. Hallazgos y pendientes

- **Campo "Enlace a evidencia" de ClickUp:** quedó vacío en 14 de las 17
  tareas del sprint por la limitación de integración señalada en §2. Este
  informe reemplaza esa función enlazando directamente cada archivo/commit
  del repositorio.
- El resto de las 16 tareas restantes tiene evidencia verificable y
  reproducible en el repositorio, consistente con lo declarado en ClickUp.
