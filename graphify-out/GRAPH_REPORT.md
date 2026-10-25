# Graph Report - Taller-de-Sistemas-Inteligentes  (2026-10-12)

## Corpus Check
- 88 files · ~472,369 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 52 file(s) not represented in the graph (top: .csv 40, (none) 8, .dvc 2)

## Summary
- 706 nodes · 944 edges · 84 communities (47 shown, 37 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9b1b25fd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- informe_sprint1.md
- Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)
- pandas
- matplotlib_pyplot
- linea_base_modelo.py
- eda_inicial.py
- eda_climatico.py
- Entorno reproducible y estado inicial de los datos (Línea Base — Paso 1)
- 3. Modelo de datos (PostgreSQL + PostGIS)
- 3. Licencias y condiciones de uso por fuente pública considerada
- eda_inicial.md
- Declaración de Uso de Inteligencia Artificial y Revisión Humana
- REGISTRO INICIAL DE RIESGOS
- 3. Requisitos funcionales
- Reglas de calidad, limpieza e imputación de datos
- Línea base y registro de experimentos (Línea Base — Paso 3)
- procesar_clima.py
- Sistema de Predicción Temprana de Brotes de Dengue/Malaria
- Controles de seguridad y privacidad
- 13. EDA integrado: clima + dengue + malaria
- Pipeline reproducible de datos (Línea Base — Paso 2)
- integrar_datos.py
- .agents/skills/openspec-explore/SKILL.md
- .claude/skills/openspec-explore/SKILL.md
- .cursor/skills/openspec-explore/SKILL.md
- Resultados de la Línea Base — lectura ordenada
- explore.md
- opsx-explore.md
- Evidencia de ejecución Scrum — Sprint 1
- Bloque de instrucciones universal (compartido con otros agentes de IA)
- Plan de Tareas — Predicción Temprana de Brotes de Dengue/Malaria
- Bloque de instrucciones universal (idéntico al de CLAUDE.md)
- Cierre de Sprint 1 — backlog pendiente, bloqueos y próximos pasos
- Team Charter
- 8. Comportamiento de las variables climáticas
- 9. Relaciones entre las variables climáticas
- Métricas de valor y criterios de éxito
- Priorización de Casos: Violencia de Género vs Dengue/Malaria
- main.py
- ADR-001: PostgreSQL 16 + PostGIS como base de datos
- ADR-003: Railway como plataforma de despliegue
- 15. Comparación conjunta entre municipios
- 17. Implicaciones para el futuro modelado
- Resumen de calidad del pipeline de datos
- 12. Comportamiento epidemiológico
- 2.1 Datos epidemiológicos
- Primer prompt para Claude Code
- 14. Resumen de relaciones clima-enfermedad
- 20. Evidencias generadas

## God Nodes (most connected - your core abstractions)
1. `main()` - 22 edges
2. `main()` - 20 edges
3. `main()` - 14 edges
4. `Controles de seguridad y privacidad` - 13 edges
5. `Declaración de Uso de Inteligencia Artificial y Revisión Humana` - 13 edges
6. `REGISTRO INICIAL DE RIESGOS` - 13 edges
7. `main()` - 12 edges
8. `3. Modelo de datos (PostgreSQL + PostGIS)` - 12 edges
9. `Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)` - 12 edges
10. `Línea base y registro de experimentos (Línea Base — Paso 3)` - 12 edges

## Surprising Connections (you probably didn't know these)
- `guardar_figura()` --calls--> `matplotlib_pyplot`  [EXTRACTED]
  scripts/eda_climatico.py →   _Bridges community 6 → community 3_
- `heatmap()` --calls--> `pandas`  [EXTRACTED]
  scripts/eda_climatico.py →   _Bridges community 6 → community 2_
- `scatter_multivariable()` --calls--> `numpy`  [EXTRACTED]
  scripts/eda_climatico.py →   _Bridges community 6 → community 4_
- `cargar_datos()` --calls--> `pandas`  [EXTRACTED]
  scripts/eda_inicial.py →   _Bridges community 5 → community 2_
- `grafico_dengue_semanal()` --calls--> `matplotlib_pyplot`  [EXTRACTED]
  scripts/eda_inicial.py →   _Bridges community 5 → community 3_

## Import Cycles
- None detected.

## Communities (84 total, 37 thin omitted)

### Community 0 - "informe_sprint1.md"
Cohesion: 0.06
Nodes (30): Bloque de reanudación, CONTEXT.md — Bitácora de sesión del proyecto, Decisiones clave, Divergencias pendientes, Preguntas abiertas (ver detalle en `design.md` §10), Registro de sesiones, ADR-002: Python 3.12 + FastAPI para el backend, Alternativas consideradas (+22 more)

### Community 1 - "Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)"
Cohesion: 0.06
Nodes (34): 10.1 EDA inicial, 10.2 EDA climatico, 10.3 EDA integrado, 10.4 Linea base, 10. Evidencias generadas, 11. Reproducibilidad, 1. Objetivo de este inventario, 2.1 Ministerio de Salud y Deportes de Bolivia — Boletin Epidemiologico N.13, 2026 (+26 more)

### Community 2 - "pandas"
Cohesion: 0.13
Nodes (18): descargar(), es_precipitacion_24h(), guardar_parcial(), main(), mostrar_resumen(), procesar_feature(), solicitar_pagina(), calcular_vecino_mas_cercano() (+10 more)

### Community 3 - "matplotlib_pyplot"
Cohesion: 0.18
Nodes (27): calidad_datos(), cargar_datos(), casos_vs_incidencia_dengue(), cobertura_vs_dengue(), composicion_malaria(), correlaciones_clima_enfermedad(), correlaciones_integradas(), crear_heatmap() (+19 more)

### Community 4 - "linea_base_modelo.py"
Cohesion: 0.15
Nodes (19): cargar_dataset_integrado(), cargar_dengue_nacional(), _cross_sectional(), experimento_a(), experimento_b(), experimento_c(), experimento_d(), grafico_comparacion_modelos() (+11 more)

### Community 5 - "eda_inicial.py"
Cohesion: 0.14
Nodes (20): analizar_calidad(), analizar_observaciones(), analizar_outliers(), cargar_datos(), _descargar_geojson_departamentos(), detectar_outliers(), dibujar_mapa_departamentos(), _encontrar_campo_nombre() (+12 more)

### Community 6 - "eda_climatico.py"
Cohesion: 0.16
Nodes (25): boxplot_variable(), boxplots(), calidad_datos(), cargar_datos(), correlaciones(), correlaciones_por_municipio(), detectar_columnas(), estadisticas_descriptivas() (+17 more)

### Community 7 - "Entorno reproducible y estado inicial de los datos (Línea Base — Paso 1)"
Cohesion: 0.09
Nodes (23): 1. Qué es este documento y por qué es el Paso 1, 2. Decisión de entorno: venv, no Docker, 3.1 Requisito de versión de Python, 3.2 Pasos de creación (reproducidos), 3.3 Resultado, 3. Entorno 1 — datos y scripts (raíz del repositorio), 4.1 Pasos de creación (los mismos que documenta el README del backend), 4.2 Resultado de `pip install -r requirements.txt` con las versiones originales: **falla** (+15 more)

### Community 8 - "3. Modelo de datos (PostgreSQL + PostGIS)"
Cohesion: 0.09
Nodes (22): 10. Preguntas abiertas, 1. Stack tecnológico, 2. Vista general de la arquitectura, 3. Modelo de datos (PostgreSQL + PostGIS), 4. Endpoints principales de la API, 5. Pipeline de predicción (motor ML), 6. Seguridad, 7. Explicabilidad del modelo (+14 more)

### Community 9 - "3. Licencias y condiciones de uso por fuente pública considerada"
Cohesion: 0.10
Nodes (20): 1. Objetivo y alcance, 2.1 Declaración, 2.2 Evidencia revisada por archivo, 2.3 Reglas del pipeline que refuerzan REQ-020, 2.4 Limitación de esta confirmación, 2. Confirmación de cumplimiento de REQ-020, 3.0 Marco general aplicable a entidades del Estado boliviano: DAT-002, 3.1 Ministerio de Salud y Deportes de Bolivia — Boletín Epidemiológico N.º 13, 2026 (+12 more)

### Community 10 - "eda_inicial.md"
Cohesion: 0.11
Nodes (17): 10. Integración de datos climáticos y epidemiológicos, 11. Cobertura del dataset integrado, 16. Limitación temporal, 18. Principales hallazgos del EDA, 19. Conclusiones, 1. Objetivo, 21. Reproducibilidad, 3. Pipeline de análisis (+9 more)

### Community 11 - "Declaración de Uso de Inteligencia Artificial y Revisión Humana"
Cohesion: 0.12
Nodes (17): 10. Evidencias del proyecto, 11. Declaración final, 1. Objetivo, 2. Herramientas de IA utilizadas por el equipo, 3. Registro de uso de IA, 4. Proceso de revisión humana, 5.1 Reproducibilidad y DVC, 5.2 Procesamiento y análisis de datos (+9 more)

### Community 12 - "REGISTRO INICIAL DE RIESGOS"
Cohesion: 0.12
Nodes (16): 10. Acciones de control implementadas o previstas, 11. Seguimiento y actualización, 1. Objetivo, 2. Categorías de riesgo, 3. Escala de Probabilidad, 4. Escala de Impacto, 5. Cálculo del nivel de riesgo, 6. Matriz de Probabilidad × Impacto (+8 more)

### Community 13 - "3. Requisitos funcionales"
Cohesion: 0.13
Nodes (15): 1. Visión general, 2. Actores / Usuarios del sistema, 3. Requisitos funcionales, 4. Requisitos no funcionales (NFR), 5. Supuestos y restricciones conocidas, 6.1 Exclusiones adicionales confirmadas por el estado real de datos (2026-09-17), 6. Fuera de alcance (versión inicial), Alertas (+7 more)

### Community 14 - "Reglas de calidad, limpieza e imputación de datos"
Cohesion: 0.13
Nodes (15): 1. Objetivo y alcance, 2. Principios, 3. Campos mínimos de trazabilidad, 4. Validaciones comunes, 5.1 Unidades y rangos, 5.2 Faltantes e imputación, 5.3 Umbrales de operación, 5. Datos climáticos (+7 more)

### Community 15 - "Línea base y registro de experimentos (Línea Base — Paso 3)"
Cohesion: 0.14
Nodes (14): 10. Limitaciones (explícitas), 11. Transparencia de IA, 1. Por qué esta entrega presenta una referencia inicial y una justificación, y no un modelo entrenado, 2. Datos usados y su carácter, 3. Baselines que la línea base deberá superar, 4. Protocolo de métricas y validación (experimento D), 5.1 Experimento A — Persistencia nacional, 5.2 Experimento B — Modelos walk-forward (nacional) (+6 more)

### Community 16 - "procesar_clima.py"
Cohesion: 0.23
Nodes (9): agregar_semana_epidemiologica(), aplicar_control_calidad(), cargar_datos(), construir_diario(), humedad_diaria(), main(), obtener_datos_validos(), precipitacion_diaria() (+1 more)

### Community 17 - "Sistema de Predicción Temprana de Brotes de Dengue/Malaria"
Cohesion: 0.15
Nodes (13): Cuándo se retoma el desarrollo del backend, Decisiones y límites, Documentación, Ejecución, Estado actual, Estructura actual, Flujo de trabajo, Instalación (+5 more)

### Community 18 - "Controles de seguridad y privacidad"
Cohesion: 0.15
Nodes (13): 10. Registro y respuesta, 11. Criterios de aceptación, 12. Revisión pendiente, 1. Objetivo y alcance, 2. Estado verificable, 3. Matriz de controles, 4. Autenticación y sesiones, 5. Autorización por roles (+5 more)

### Community 19 - "13. EDA integrado: clima + dengue + malaria"
Cohesion: 0.15
Nodes (13): 13.1 Temperatura y dengue, 13.2 Humedad y dengue, 13.3 Precipitación y dengue, 13.4 Temperatura y malaria, 13.5 Humedad y malaria, 13.6 Precipitación y malaria, 13. EDA integrado: clima + dengue + malaria, Hallazgo (+5 more)

### Community 20 - "Pipeline reproducible de datos (Línea Base — Paso 2)"
Cohesion: 0.15
Nodes (13): 1. Qué problema resuelve este pipeline, 2.1 Validación epidemiológica, 2.2 Calendario diario global, 2.3 Imputación climática, 2.4 Reagregación semanal con nivel de confianza, 2. Qué hace, en orden, 3. Resultado obtenido (última ejecución), 4. Reproducibilidad (+5 more)

### Community 21 - "integrar_datos.py"
Cohesion: 0.29
Nodes (9): cargar_datos(), guardar(), integrar(), main(), normalizar_municipios(), preparar_dengue(), preparar_malaria(), resumir_clima() (+1 more)

### Community 22 - ".agents/skills/openspec-explore/SKILL.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 23 - ".claude/skills/openspec-explore/SKILL.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 24 - ".cursor/skills/openspec-explore/SKILL.md"
Cohesion: 0.18
Nodes (10): Check for context, Ending Discovery, Guardrails, Handling Different Entry Points, OpenSpec Awareness, The Stance, What You Don't Have To Do, What You Might Do (+2 more)

### Community 25 - "Resultados de la Línea Base — lectura ordenada"
Cohesion: 0.18
Nodes (11): 1. Resumen ejecutivo (4 experimentos), 2. Conceptos previos (cómo leer los gráficos), 3. Experimento A — Persistencia nacional, 4. Experimento B — Modelos walk-forward (nacional), 5. Experimento C — Regresión cross-sectional municipal (fallo documentado), 6. Experimento D — Protocolo (lista de espera), 7. Archivos generados, ¿Para qué sirve cada modelo comparado? (+3 more)

### Community 26 - "explore.md"
Cohesion: 0.20
Nodes (9): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, The Stance, What You Don't Have To Do, What You Might Do, When a change exists (+1 more)

### Community 27 - "opsx-explore.md"
Cohesion: 0.20
Nodes (9): Check for context, Ending Discovery, Guardrails, OpenSpec Awareness, The Stance, What You Don't Have To Do, What You Might Do, When a change exists (+1 more)

### Community 28 - "Evidencia de ejecución Scrum — Sprint 1"
Cohesion: 0.20
Nodes (10): 1. Product Goal vigente, 2. Backlog priorizado en ClickUp, 3. Resumen del estado (verificado contra el repositorio, no solo ClickUp), 4. Carril: Discovery, 5. Carril: Data, 6. Carril: Architecture, 7. Carril: Build / QA / Deploy, 8. Carril: Risk (+2 more)

### Community 29 - "Bloque de instrucciones universal (compartido con otros agentes de IA)"
Cohesion: 0.22
Nodes (8): Bloque de instrucciones universal (compartido con otros agentes de IA), CLAUDE.md — Instrucciones para Claude Code, Flujo de trabajo esperado, Instrucciones específicas de Claude Code, Manejo de datos incompletos (contexto específico del dominio), Proyecto, Reglas no negociables, Stack

### Community 30 - "Plan de Tareas — Predicción Temprana de Brotes de Dengue/Malaria"
Cohesion: 0.22
Nodes (8): Fase 1 — Infraestructura base, Fase 2 — Capa de datos, Fase 3 — Lógica de negocio / motor de predicción, Fase 4 — Capa de API, Fase 5 — Dashboard (frontend), Fase 6 — Pruebas y validación, Notas de alcance, Plan de Tareas — Predicción Temprana de Brotes de Dengue/Malaria

### Community 31 - "Bloque de instrucciones universal (idéntico al de CLAUDE.md)"
Cohesion: 0.25
Nodes (7): Bloque de instrucciones universal (idéntico al de CLAUDE.md), Instrucciones para GitHub Copilot, Manejo de datos incompletos, Notas específicas para Copilot, Proyecto, Reglas no negociables, Stack

### Community 32 - "Cierre de Sprint 1 — backlog pendiente, bloqueos y próximos pasos"
Cohesion: 0.25
Nodes (8): 1. Estado real de las 17 tareas de Sprint 1, 2. Backlog pendiente para el siguiente sprint, 3.1 Acceso a DVC — RESUELTO, 3.2 Fuentes epidemiológicas semanales por municipio, 3.3 Catálogo oficial de municipios de Bolivia, 3. Bloqueos actuales y plan de resolución, 4. Viabilidad del proyecto (evaluación breve), Cierre de Sprint 1 — backlog pendiente, bloqueos y próximos pasos

### Community 33 - "Team Charter"
Cohesion: 0.25
Nodes (7): Canales y tiempos de respuesta, Definition of Done inicial, Integrantes y disponibilidad, Manejo de bloqueos, Reglas de integridad y uso de IA, Revisión de PR, Team Charter

### Community 34 - "8. Comportamiento de las variables climáticas"
Cohesion: 0.29
Nodes (7): 8.1 Temperatura, 8.2 Humedad relativa, 8.3 Precipitación, 8. Comportamiento de las variables climáticas, Hallazgo, Hallazgo, Hallazgo

### Community 35 - "9. Relaciones entre las variables climáticas"
Cohesion: 0.29
Nodes (7): 9.1 Temperatura y humedad, 9.2 Temperatura y precipitación, 9.3 Humedad y precipitación, 9. Relaciones entre las variables climáticas, Hallazgo, Hallazgo, Hallazgo

### Community 36 - "Métricas de valor y criterios de éxito"
Cohesion: 0.29
Nodes (7): 1. Por qué se separan dos conjuntos de métricas, 2. Métricas del sistema final, 3. Métricas de esta entrega (evidencia real, ya medida), 4. Qué falta para poder medir NFR-001/NFR-002 con datos reales, 5. Nota sobre el pipeline de limpieza, Inconsistencia detectada y corregida, Métricas de valor y criterios de éxito

### Community 37 - "Priorización de Casos: Violencia de Género vs Dengue/Malaria"
Cohesion: 0.29
Nodes (6): **CASO 1: Detección Automática de Violencia de Género en Llamadas**, **CASO 2: Predicción de Brotes de Dengue/Malaria**, Detalles de Evaluación, LAB_01 - Taller de Sistemas Inteligentes, Matriz de Evaluación, Priorización de Casos: Violencia de Género vs Dengue/Malaria

### Community 39 - "ADR-001: PostgreSQL 16 + PostGIS como base de datos"
Cohesion: 0.33
Nodes (6): ADR-001: PostgreSQL 16 + PostGIS como base de datos, Alternativas consideradas, Consecuencias, Contexto, Decisión, Justificación

### Community 40 - "ADR-003: Railway como plataforma de despliegue"
Cohesion: 0.33
Nodes (6): ADR-003: Railway como plataforma de despliegue, Alternativas consideradas, Consecuencias, Contexto, Decisión, Justificación

### Community 41 - "15. Comparación conjunta entre municipios"
Cohesion: 0.33
Nodes (6): 15. Comparación conjunta entre municipios, Guayaramerín, Hallazgo, Ixiamas, Palos Blancos, San Buenaventura

### Community 42 - "17. Implicaciones para el futuro modelado"
Cohesion: 0.33
Nodes (6): 17.1 Mantener la dimensión temporal, 17.2 Crear variables rezagadas, 17.3 Considerar la cobertura de datos, 17.4 Mantener la variable municipio, 17.5 Tratar dengue y malaria de forma diferenciada, 17. Implicaciones para el futuro modelado

### Community 43 - "Resumen de calidad del pipeline de datos"
Cohesion: 0.40
Nodes (4): Clima, Epidemiologia, Reglas no aplicables con los datos actuales, Resumen de calidad del pipeline de datos

### Community 44 - "12. Comportamiento epidemiológico"
Cohesion: 0.40
Nodes (5): 12.1 Dengue, 12.2 Malaria, 12. Comportamiento epidemiológico, Hallazgo, Hallazgo

### Community 45 - "2.1 Datos epidemiológicos"
Cohesion: 0.40
Nodes (5): 2.1 Datos epidemiológicos, 2.2 Datos climáticos, 2. Fuentes de datos, Dengue, Malaria

### Community 47 - "14. Resumen de relaciones clima-enfermedad"
Cohesion: 0.67
Nodes (3): 14.1 Relación entre casos e incidencia de dengue, 14.2 Diferencias entre Pearson y Spearman, 14. Resumen de relaciones clima-enfermedad

### Community 48 - "20. Evidencias generadas"
Cohesion: 0.67
Nodes (3): 20.1 EDA climático, 20.2 EDA integrado, 20. Evidencias generadas

## Knowledge Gaps
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)` connect `Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)` to `informe_sprint1.md`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Should `informe_sprint1.md` be split into smaller, more focused modules?**
  _Cohesion score 0.0573025856044724 - nodes in this community are weakly interconnected._
- **Why does `Entorno reproducible y estado inicial de los datos (Línea Base — Paso 1)` connect `Entorno reproducible y estado inicial de los datos (Línea Base — Paso 1)` to `informe_sprint1.md`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Should `Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)` be split into smaller, more focused modules?**
  _Cohesion score 0.058823529411764705 - nodes in this community are weakly interconnected._
- **Why does `Diseño del Sistema — Predicción Temprana de Brotes de Dengue/Malaria` connect `3. Modelo de datos (PostgreSQL + PostGIS)` to `informe_sprint1.md`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `pandas` be split into smaller, more focused modules?**
  _Cohesion score 0.12701612903225806 - nodes in this community are weakly interconnected._
- **Should `eda_inicial.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13756613756613756 - nodes in this community are weakly interconnected._