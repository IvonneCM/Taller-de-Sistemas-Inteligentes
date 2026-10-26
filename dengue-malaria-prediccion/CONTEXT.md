# CONTEXT.md — Bitácora completa del proyecto

> Este archivo reemplaza al `CONTEXT.md` anterior. Léelo primero, en cada
> sesión nueva, antes de tocar código — así lo pide `CLAUDE.md`.

---

## 1. Qué es este proyecto

**Sistema Inteligente de Predicción Temprana de Brotes de Dengue/Malaria**
— proyecto universitario para la materia **Taller de Sistemas
Inteligentes**, equipo de 5 personas.

**Objetivo del producto:** predecir zonas con riesgo de brote de dengue o
malaria en Bolivia con **3-4 semanas de anticipación**, usando datos
epidemiológicos, climáticos y geoespaciales, para activar campañas de
fumigación preventiva y asignar recursos médicos antes de que ocurra el
brote.

**Usuarios:** autoridades de salud pública, equipos de prevención del
SEDES, médicos epidemiólogos, coordinadores sanitarios municipales.

**Equipo (ClickUp):** Tania Perez, Ivonne Colque, Adriana Rocha Vedia,
Dilan Mamani Pamuri, Ignacio Retamozo Torrez. (Roger aparece en el
workspace pero nunca se le asignó tarea — probablemente el docente/facilitador.)

**Repositorio:** `github.com/IvonneCM/Taller-de-Sistemas-Inteligentes`,
rama **`tani`**, todo el proyecto vive en el subdirectorio
`dengue-malaria-prediccion/`.

**Stack:**
- Backend: Python 3.12 + FastAPI
- Base de datos: PostgreSQL 16 + PostGIS
- ML: scikit-learn / XGBoost + SHAP (explicabilidad), pipeline batch semanal
- Frontend: React + Leaflet/Mapbox
- Despliegue: Railway · Entrenamiento offline: Google Colab
- Agentes de IA usados en el proyecto: Claude Code + GitHub Copilot

---

## 2. Metodología: Spec Driven Development (SDD)

Se siguió un flujo de documentación-antes-que-código:

```
Solicitud de cambio → requirements.md → design.md → tasks.md →
configuración de agentes IA (CLAUDE.md / copilot-instructions.md) → CONTEXT.md
```

Reglas no negociables (ya en `CLAUDE.md`, no repetirlas aquí en detalle):
no inventar datos reales no verificados, no datos personales de pacientes,
no alertas sin justificación, tabla `predicciones` inmutable,
`requirements.md` es la fuente de autoridad, no exponer credenciales.

---

## 3. La evaluación del docente (lo más importante para las próximas 2-3 semanas)

Esta es la **primera evaluación** del proyecto, con una rúbrica específica
que el docente compartió en clase. Puntos clave:

> **"No se espera el sistema final completo, sino decisiones iniciales
> justificadas, trazables y viables."**

**Secuencia obligatoria de la presentación (7 puntos, en este orden):**
1. Problema y Contexto
2. Product Goal y Valor
3. Datos
4. Arquitectura
5. Riesgos y Seguridad
6. Línea Base y Evidencia
7. Gestión y Cierre

**Checklist que el docente revisará en vivo:**
| Punto | Debe estar listo cuando... |
|---|---|
| README | Actualizado, con instrucciones para reproducir el avance |
| Definiciones | Problema, métricas, exclusiones y criterios de éxito documentados |
| Datos | Inventario, EDA/perfilado, calidad y reglas de preparación documentados |
| Arquitectura y Riesgos | Modelos C4, ADRs documentados, Risk Register inicial |
| Scrum | Product Goal, Backlog priorizado, evidencia de trabajo del sprint |
| Línea Base | Scripts/pipeline reproducible y registro de experimentos |
| Uso de IA | Declaración transparente de qué IA se usó + evidencia de revisión humana |

**Reglas que el docente aplica activamente:**
- Regla de evidencia: sin resultados aún → presentar la justificación técnica de cómo se establecerá la línea base, no dejarlo en blanco.
- Un experimento fallido SÍ es evidencia válida si está documentado y se usó para decidir.
- Un diagrama no basta — toda decisión técnica debe justificarse frente al problema, los datos y la viabilidad.
- Transparencia de IA obligatoria (no se penaliza usar IA, sí ocultarlo).

---

## 4. Qué existe ya en el repositorio (todo generado, pendiente de commit/push)

### Documentación base (raíz de `dengue-malaria-prediccion/`)
- `requirements.md` — 20 REQ + 10 NFR, cada uno con criterio de aceptación
- `design.md` — arquitectura completa, modelo de datos, endpoints, §10 con preguntas abiertas
- `tasks.md` — 36 tareas atómicas en 6 fases (esto es el plan de **desarrollo del backend**, posterior a esta primera evaluación)
- `CLAUDE.md` / `.github/copilot-instructions.md` — reglas para agentes de IA
- `README.md`, `.env.example`, `.gitignore`, `requirements.txt`
- `.vscode/` (settings, launch, tasks, extensions) — paquete de trabajo para VS Code
- `FIRST_PROMPT.md` — primer prompt para arrancar TASK-001 cuando toque desarrollo
- `app/` — esqueleto de carpetas FastAPI (solo `__init__.py` y un `main.py` mínimo con `/health`)

### `docs/`
- `docs/c4/` — Diagramas C4 Nivel 1 (Contexto) y Nivel 2 (Contenedores), en `.svg` y `.png`, más `README.md` con la justificación de cada decisión frente al problema/datos/viabilidad
- `docs/metricas_valor.md` — métricas del sistema final (NFR-001/002) vs. métricas de valor de esta entrega
- `docs/cierre_sprint1.md` — backlog pendiente, bloqueos, viabilidad, próximos pasos (insumo del punto 7 de la presentación)
- `docs/eda_inicial.md` + `docs/eda_summary.json` + `docs/eda_assets/*.png` — EDA inicial sobre datos **sintéticos** (ver §6)
- `docs/pipeline_datos.md` + `docs/pipeline_summary.json` — pipeline reproducible de limpieza/imputación

### `notebooks/`
- `00_generar_datos_sinteticos.py` — genera datos sintéticos con la estructura de SEDES/SENAMHI (semilla fija = reproducible)
- `01_eda_inicial.py` — perfilado (cobertura, outliers, distribuciones)
- `02_pipeline_limpieza.py` — limpieza + imputación, produce `data/processed/*.csv`

### `data/` (gitignored — se regeneran corriendo los scripts, no se versionan)
- `data/raw/` — datos sintéticos crudos
- `data/processed/` — datos ya limpios/imputados

### Fuera del repo (entregados a Tania como archivos, no forman parte del código)
- Deck de 11 slides (.pptx) resumiendo todo el proceso SDD
- PDF "Guía para la Defensa" con las tareas de cada persona y checklist

---

## 5. Backlog en ClickUp (espacio "Taller de Sistemas Inteligentes")

**Listas:** Discovery, Data, Architecture, Risk, Build/QA/Deploy (+ carpeta
"Información del Equipo" y "Ceremonies/Meeting Tracker", sin tareas).

**Campos personalizados en todas las tareas:** Criterio de aceptación,
Enlace a evidencia, Estado de bloqueo, Riesgo asociado, Sprint.

- **Sprint 0** (9 tareas en Discovery): Team Charter, Product Goal,
  priorización de casos, requisitos con OpenSpec, diseño técnico,
  generación de proyecto base, plan de implementación, config. de Claude
  Code, config. de ClickUp — **todas en estado Done**.
- **Sprint 1** (17 tareas nuevas, repartidas entre los 5): cubren
  exactamente los huecos del checklist del docente (métricas, alcance,
  uso de IA, README, inventario de datos, EDA, reglas de calidad,
  privacidad, C4, ADR, Risk Register, seguridad, Línea Base en 3 pasos,
  evidencia de sprint, cierre).

### Las 4 tareas de Tania (Sprint 1) y su estado real

| Tarea | Lista | Estado en ClickUp | Estado real |
|---|---|---|---|
| Documentar métricas de valor y criterios de éxito | Discovery | **Done** | Completa — `docs/metricas_valor.md` |
| Preparar cierre: backlog, bloqueos, próximos pasos | Discovery | **Done** | Completa — `docs/cierre_sprint1.md` |
| Elaborar diagramas C4 (Contexto y Contenedores) | Architecture | **Done** | Completa — `docs/c4/` |
| Construir pipeline reproducible de datos (Línea Base — Paso 2) | Build/QA/Deploy | **Sin marcar** (sigue en backlog) | **Contenido ya construido** (`notebooks/02_pipeline_limpieza.py`, `docs/pipeline_datos.md`) — falta subir al repo y marcar Done en ClickUp |

**Importante:** el EDA inicial (`docs/eda_inicial.md`, notebooks 00 y 01) es
la tarea de **Adriana**, no de Tania — se construyó de forma adelantada
para desbloquear el pipeline de Tania, que dependía de él. Avisar a
Adriana antes de que ella suba/reclame ese entregable como propio, o
decidir juntas cómo se reparte el crédito.

---

## 6. Decisiones y supuestos clave (para no repetir el razonamiento)

- **Fuente de datos:** el curso (LAB_01/"CASO D") ya identificó **SEDES**
  (epidemiológico) y **SENAMHI** (climático) como las fuentes objetivo,
  elegidas por acceso más viable — pero el **acceso real aún no está
  confirmado**. Por eso todo el EDA y el pipeline corren sobre datos
  **sintéticos** con la misma estructura, dejándolo explícito en cada
  documento.
- **Zona piloto:** aún no seleccionada. Bloquea la validación real de
  NFR-001 (75% precisión espacial) y NFR-002 (2 semanas de anticipación).
- **Regla de limpieza pendiente de confirmar con Dilan:** un outlier en
  `casos_confirmados` (posible brote real) NO se limpia automáticamente —
  solo se marca `posible_senal_brote=True`. Esto está implementado en el
  pipeline de Tania pero falta que Dilan lo confirme en su tarea de
  "Definir reglas de calidad, limpieza e imputación de datos".
- **Limitación conocida del pipeline:** el reindexado de calendario se
  hace por grupo (municipio/enfermedad), no contra un calendario global
  fijo — puede haber un desfase de 1 fila entre grupos. Documentado en
  `docs/pipeline_datos.md` §5, pendiente de arreglar antes de usar datos reales.
- **`tasks.md` (36 tareas, 6 fases) es el plan de desarrollo del backend
  real** — es POSTERIOR a esta primera evaluación. No hay que empezarlo
  todavía; la evaluación actual es sobre documentación/decisiones, no
  sobre código funcionando.

---

## 7. Próximos pasos inmediatos (en orden)

1. **Verificar y hacer commit/push de todo lo ya generado** a la rama
   `tani` (todo lo descrito en §4 ya existe como archivos, solo falta
   confirmarlo en el repo real de Tania).
2. **Actualizar el campo "Enlace a evidencia"** de las 3 tareas ya
   marcadas Done, y marcar como Done la 4ª (pipeline) una vez esté en el
   repo.
3. **Coordinar con el equipo** las piezas que aún dependen de otras
   personas: Risk Register y controles de seguridad (Adriana/Dilan),
   Línea Base Pasos 1 y 3 (Ignacio/Ivonne), confirmación de la regla de
   limpieza de outliers (Dilan).
4. **Resolver, como equipo,** las preguntas abiertas de la sección 6 antes
   de la defensa (fuente real de datos, zona piloto) — o decidir
   explícitamente presentar con datos sintéticos y justificarlo (es una
   opción válida según la Regla de Evidencia del docente).
5. **Ensayar la secuencia de 7 puntos** de la presentación con el
   contenido de la sección 3 de este documento.
6. Solo **después** de la defensa: retomar `tasks.md` desde TASK-001 con
   `FIRST_PROMPT.md` para empezar el desarrollo real del backend.

---

## 8. Cómo debe trabajar Claude Code a partir de aquí

Seguir el protocolo ya definido en `CLAUDE.md`: leer este archivo primero,
confirmar la tarea activa antes de programar, una tarea atómica a la vez,
preguntar ante cualquier ambigüedad en vez de asumir, y actualizar este
`CONTEXT.md` al cerrar cada sesión (nueva entrada en un futuro "Registro de
sesiones", decisiones nuevas, bloqueos resueltos o nuevos).

Si el pedido inmediato de Tania es "sube esto al repo", el trabajo es
`git add / commit / push` sobre lo ya generado (§4) — no generar contenido
nuevo. Si pide continuar con tareas pendientes del equipo, seguir el
backlog de la sección 5.

---

## 9. Registro de sesiones

### 2026-10-25 — TASK-012 baseline XGBoost de dengue

**Estado:** implementación terminada, verificada y `TASK-012` marcada como
`[x]` en `tasks.md`. Solo falta que Ivonne revise y haga el commit.

**Implementado**
- `app/ml/entrenamiento.py`: etiqueta `casos_dengue_t_mas_{3,4} > 0`,
  walk-forward cronológico, XGBoost, métricas, baselines, artefactos JSON y
  registro opcional en BD.
- `tests/ml/test_entrenamiento.py`: 11 pruebas; suite `tests/ml` completa
  ejecutada con **33 OK, 1 omitida** (pandas 2.2.3 ausente).
- `app/ml/artifacts/`: boosters y metadata de t+3 y t+4, versión `v1`.
- `app/models/modelo.py` + `app/models/__init__.py`: ORM de `modelos`.
- `alembic/versions/4079b097a5a2_task_012_modelos.py`: crea solo `modelos`.
- `alembic/env.py`: exclusión dinámica de tablas/índices de extensiones
  PostGIS en autogenerate. La consulta cierra su transacción implícita con
  `rollback()` antes de iniciar la migración; sin eso, el DDL se revertía.
- `docs/task_012_baseline.md` y `docs/task_012_metricas.json`.
- `scripts/graficos_task_012.py` y `scripts/task_012_output/`: 6 gráficos
  (métricas, matrices de confusión, ROC/PR, por origen, distribución de
  probabilidades e importancia de variables), predicciones walk-forward y
  CSVs de métricas. El script verifica que el recálculo coincida con la
  metadata de los artefactos.

**Datos y protocolo**
- Panel `data/processed/panel_semanal_dengue_clima.csv`: 364 filas,
  28 municipios, 13 semanas de 2026, 24 features.
- Orígenes t+3: 2026-02-09/16/23 y 03-02 (112 predicciones).
- Orígenes t+4: 2026-02-16 y 02-23 (56 predicciones).
- Filas del modelo final: 224 (t+3) y 196 (t+4).

**Resultados (macro por origen)**
- t+3: modelo F1 0.3322 / ROC-AUC 0.6588; regla `casos_recientes`
  F1 0.4775 / ROC-AUC 0.6913. El modelo **no supera** la regla simple.
- t+4: modelo F1 0.3785 / ROC-AUC 0.6268; regla `casos_recientes`
  F1 0.3255 / ROC-AUC 0.6215. Mejora marginal, no concluyente.
- Métricas exploratorias; no validan NFR-001/NFR-002. La etiqueta no es
  definición de brote.

**Verificación BD (PostGIS temporal en Docker)**
- `alembic upgrade head` aplicado; `alembic check` sin operaciones nuevas.
- Upgrade desde base vacía verificado (con `CREATE EXTENSION postgis`
  previo; la migración base no crea la extensión).
- Catálogo: 2 enfermedades, 4 municipios piloto.
- Filas en `modelos`: id 1 (t+3), id 2 (t+4), `enfermedad_id=1`,
  `metricas_entrenamiento` JSONB válido.

**Pendientes**
- Ivonne debe revisar y hacer el commit/push (instrucción explícita: el
  agente no commitea).
- La rama local `ivonne2` sigue detrás de `origin/ivonne2`; no se hizo
  commit ni push.
- `.gitignore` tiene un cambio previo no relacionado (ignora
  `Reparto de Tarea.md`); no tocarlo sin decidir si se conserva.
