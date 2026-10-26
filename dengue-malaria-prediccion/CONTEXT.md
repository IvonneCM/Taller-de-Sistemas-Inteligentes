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

### 2026-10-26 (noche) — Integración y defensa del MVP (TASK-037 a 048, Dilan)

**Estado:** implementado y verificado en local: **345 tests del backend, 108 de la
interfaz**, 80 % de cobertura en `app/etl` + `app/ml`, `alembic check` limpio.
Todo sin commit al cerrar esta entrada. Motivo: la «Guía de Defensa del MVP»
exige un sistema integrado, desplegado, reproducible y respaldado por evidencia;
se contrastó con el repositorio y se agregaron las tareas que faltaban (Fase 7 de
`tasks.md`).

**Hecho**
- `app/core/observabilidad.py` + `app/api/routes/health.py` (TASK-040): `X-Request-ID`,
  logs sin secretos, 503 ante base caída, `/health/ready`, timeouts de conexión y consulta.
- `app/etl/seed_demo.py` (TASK-038): un comando carga casos reales, modelo, predicciones
  y usuarios demo. `tests/e2e/` (TASK-039) y `scripts/smoke_test.py`.
- `GET /casos/resumen` (TASK-047) para mostrar la malaria (solo acumulados, ADR-005).
- Interfaz React (`frontend/`): login, mapa, detalle por rol, alertas, historial;
  sistema de diseño estilo Apple con malaria como entrada (TASK-037, 048, 028 y parte
  de 027, 029, 030). Pruebas con Vitest, incluido el contraste de los colores.
- Documentos: `arquitectura_actual.md`, `resultados_experimentales.md`,
  `guion_demo_y_plan_b.md`, riesgos M-01 a M-14 en `risk_register.md`,
  `contrato_api.md` al día, `.github/workflows/ci.yml` (sin ejecutar en GitHub).
- `tests/conftest.py`: cada test parte de las tablas de datos vacías (dentro de la
  transacción que se revierte), para poder correrlos contra una base con la demo cargada.

**Decisiones a confirmar con el equipo**
- La malaria es la vista de entrada pero **sin predicciones**: casos observados.
- `refresh_token` en `sessionStorage` (riesgo M-11); access token en memoria.
- Regla de «acierto» del historial: ±7 días (ya anotada en `contrato_api.md`).

**Docker (verificado 2026-10-26, Colima en Apple Silicon):** las 3 imágenes
construyen, `docker compose` migra y carga la demo, el humo pasa por la API y por
nginx, y los 283 tests pasan contra PostgreSQL 16 + PostGIS 3.4 (como el CI).
Hallazgo: `app/services/casos.py` importaba `pandas` y la imagen `api` no lo trae
(la API no arrancaba); corregido moviendo las constantes a `app/etl/fuentes.py` y
vigilado por `tests/test_api_ligera.py`. La imagen de la base solo es amd64.

**Integraciones posteriores (2026-10-26):** TASK-015 (Ivonne) y TASK-024/025 (Adriana) integradas en `dilan`. Las pruebas de integración de Adriana venían omitidas (necesitan una base exclusiva): corridas contra PostgreSQL, 46 de 46 pasan; el CI ya las ejecuta. Se agregó la pestaña «Campañas» (TASK-031) y un E2E por rol.

**Pendientes (no son de esta sesión)**
1. TASK-004 despliegue (bloquea el gate obligatorio) y decidir proveedor.
2. TASK-016 (tarea semanal). TASK-015 ya la entregó Ivonne y está integrada: con el umbral por defecto (70 %) ninguna predicción alerta; el equipo de salud debe fijar el umbral real.
3. Fuente de `brotes_confirmados` (riesgo M-08).
4. TASK-027: selector de agregación; TASK-029: filtro de fechas en pantalla; TASK-026, 033, 034, 035, 036.
5. TASK-041 (tag) y 045 (ensayo, grabación, respaldo). La CI (046) ya corrió en verde en GitHub.
6. Entorno: crear el venv fuera de carpetas sincronizadas con iCloud. En Mac,
   `xgboost-cpu` de `requirements-ml.txt` no se instala: usar `xgboost==2.1.1`.

### 2026-10-26 — API de zonas y alertas (TASK-019 a TASK-023, Dilan)

**Estado:** implementado y verificado contra PostgreSQL 17 + PostGIS 3.6
locales (`pytest tests/api tests/test_modelos_predicciones.py`: 133 tests en
verde; `alembic upgrade head`, `downgrade` y `alembic check` sin diferencias).
**Sin commit ni push** de este trabajo. TASK-019 a 022 marcadas `[x]`;
TASK-023 queda sin marcar (ver pendientes).

**Implementado**
- Modelos y migración `7c1e5d9a3b42`: `predicciones`, `alertas`,
  `umbrales_configuracion`, `brotes_confirmados` (nadie las tenía asignadas;
  divergencias anotadas en `design.md` §3 antes de marcar las tareas).
- `app/api/deps.py`: verifica el JWT de acceso y el rol (`get_usuario_actual`,
  `require_role`). No emite tokens (TASK-017) ni toca `roles`/`usuarios`.
- `app/services/` (consultas y reglas por rol), `app/schemas/` y
  `app/api/routes/{zonas,alertas,admin}.py`; `app/main.py` los registra.
- `docs/contrato_api.md`: el "borrador de la API" del día 1 (rutas, payloads y
  claims del token), además de `docs/contrato_esquema_bd.md` ampliado.
- Pruebas en `tests/api/` y `tests/test_modelos_predicciones.py`. El fixture
  `catalogo` pasó a `tests/conftest.py`; ahora `conftest.py` fija `SECRET_KEY`
  solo para pruebas.

**Decisiones que este diseño no fijaba (confirmar con el equipo)**
- Vista completa de predicción: `epidemiologo` y `admin`; `autoridad`, `sedes`
  y `coordinador_municipal` reciben la resumida.
- Umbral por defecto 70 % (referencial, ejemplo de REQ-009).
- Correlación predicción↔brote: ±7 días de `fecha_estimada_riesgo`.
- `app/main.py` ahora importa `app.core.database`, por lo que arrancar la API
  exige `DATABASE_URL` (antes `/health` arrancaba sin ella).

**Pendientes**
1. Ivonne: `/auth/login` debe emitir los claims de `docs/contrato_api.md`;
   `evaluacion_alertas` (TASK-015) debe leer `obtener_umbral` y TASK-014 debe
   insertar en `predicciones` (variables como lista). Seed de `roles`.
2. Quién carga `brotes_confirmados` (sin fuente asignada): sin datos, el
   historial y TASK-034 quedan vacíos.
3. TASK-032: cobertura medida 2026-10-26 sobre `app/etl` + `app/ml`: **86 %**
   total (205 tests en verde; `entrenamiento.py` 75 %, el resto ≥ 84 %).
   Falta `prediccion.py` (TASK-014, Ivonne): al existir, repetir
   `pytest --cov=app/etl --cov=app/ml` y marcar la tarea.
4. TASK-031 y TASK-035 dependen de Adriana (024/025) y del cierre del resto.
5. Entorno: Python 3.12 (`pip install -r requirements.txt` no funciona en
   3.14). No crear el venv dentro de una carpeta sincronizada con iCloud
   (`Documents`): los imports se cuelgan. Se usó `~/.venvs/dengue-malaria` y
   el repo en `~/Pictures/machine/`. Suite completa: ~11 s.

> Los registros siguientes conservan los avances, verificaciones y
> pendientes tal como se documentaron en cada sesión y rama. Las notas
> sobre commits o estados locales corresponden a ese momento.
> Los pendientes de una sesión pueden quedar resueltos en entradas
> posteriores; estas notas históricas no sustituyen el estado actual
> de `tasks.md` ni el código integrado.

### 2026-10-25 — Capa de datos (TASK-005 a TASK-010) verificada en PostGIS real

> Nota: las secciones 4 a 7 de arriba describen el estado de la primera
> evaluación (datos sintéticos, backend en pausa) y están desactualizadas.
> Para el estado actual, ver esta entrada, `tasks.md` y `design.md`.

**Hecho**
- Se levantó PostgreSQL 16 + PostGIS 3.4 en Docker (`postgis/postgis:16-3.4`,
  puerto 5433 porque el 5432 lo usa PostgreSQL de Homebrew) y se verificó:
  `alembic upgrade head`, geometría `MultiPolygon,4326` con índice GIST,
  `CHECK >= 0` y `UNIQUE(municipio_id, fecha)` rechazando datos inválidos,
  y 23 tests en verde (`DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/dengue_malaria`).
- TASK-005 a TASK-010 marcadas `[x]` en `tasks.md`, con su verificación anotada.
- TASK-009 corregida: ahora ingiere dengue como serie SEMANAL
  (`ingerir_dengue_semanal`, decisión 2 del reparto). Antes solo ingería el
  acumulado SE1-13 y decía que no había serie semanal.
- Publicado `docs/contrato_esquema_bd.md` (esquema de BD para Ivonne y Dilan).
- Pipeline de datos de un solo comando (`scripts/pipeline_completo.py`, 10
  pasos) y paneles para el modelo (`data/processed/panel_semanal_dengue_clima.csv`,
  `panel_bloques_malaria_clima.csv`); ver `docs/guia_entrega_fase2.md`.

**Divergencias respecto a `design.md` (ya anotadas en `design.md` §3 y §10)**
- `fecha_ingesta` es `timestamptz`; `es_dato_imputado` es NOT NULL; hay un
  `UNIQUE` extra en `casos_epidemiologicos`.
- `fecha_reporte` = domingo de la semana ISO en filas semanales (dengue) y
  cierre del periodo en filas acumuladas (malaria).

**Bug encontrado solo con PostgreSQL real:** un texto de `fuente` de más de
100 caracteres falla con `StringDataRightTruncation` (la columna es
`VARCHAR(100)`). Corregido y cubierto por un test que no necesita BD.

**Pendiente / decisiones abiertas**
1. ~~**Malaria:** decidir cómo guardarla.~~ **Resuelto (ADR-005):** acumulado
   SE1-13 en la BD (3 filas piloto, sin semanas inventadas); el modelo de
   malaria entrena con `data/processed/panel_bloques_malaria_clima.csv`. Se
   reabre si SEDES/SNIS entrega casos semanales.
2. **Tabla `roles` vacía:** el seed no carga los roles de `design.md` (la
   necesita TASK-017/018, Ivonne).
3. **`municipios.nombre` no es UNIQUE:** ambiguo al ampliar el catálogo más
   allá de los 4 municipios piloto; ampliarlo exige polígonos oficiales.
4. **TASK-027** (mapa de calor) no se puede empezar: depende de
   `GET /zonas/riesgo` (Dilan, TASK-019) y no hay frontend en el repo.
5. **Sin commit:** el pipeline de datos y sus CSV ya están versionados
   (commit `89202f0`). Quedan sin versionar, en la rama
   `tania/task-005-010-capa-datos`: los cambios del backend (conector y
   tests de TASK-009, `tests/test_modelo_usuarios.py`), `tasks.md`,
   `design.md`, este archivo y `docs/contrato_esquema_bd.md`.

### 2026-10-25 (2) — Fase 1: TASK-001 a TASK-003 implementadas, TASK-004 a medias

> TASK-001 a TASK-003 cerradas `[x]` (el usuario pidió cerrarlas tras la
> verificación; no hay divergencia con `design.md`). TASK-004 queda abierta: el
> despliegue en la nube se pospone.

**Hecho**
- TASK-001: `requirements.txt` ya traía todo; `pip install -r` en un venv limpio
  termina con exit 0 y `pip check` sin conflictos. Todas las dependencias
  tienen wheel para Linux/Python 3.12.
- TASK-002: `docker-compose.yml` nuevo (servicio `db`, `postgis/postgis:16-3.4`,
  puerto del host 5433 por defecto y configurable). `SELECT PostGIS_Version();`
  devuelve 3.4. No existía ningún Dockerfile ni compose antes.
- TASK-003: `app/core/config.py` (pydantic-settings) con las 6 variables.
  `DATABASE_URL` y `SECRET_KEY` son obligatorias; en `production` se rechaza
  una `SECRET_KEY` de ejemplo o de menos de 32 caracteres. `database.py` y
  `alembic/env.py` ahora leen de ahí (antes `os.environ`). `tests/test_config.py`
  (3 tests). 27 tests en verde con la BD de compose.
- TASK-004 (parcial): `Dockerfile` (Python **3.12** fijado, usuario no root,
  escucha en `$PORT`), `.dockerignore`, `railway.toml` (healthcheck `/health`).
  En local, `docker compose up --build` responde 200 en `/health`.

**Imágenes de Docker (misma sesión, después del cierre de TASK-004 local)**
- La imagen única pesaba 2,4 GB (469 MB eran librerías de GPU de NVIDIA que trae
  `xgboost`). Se dividió en `Dockerfile` con targets `api` (323 MB) y `ml`
  (1,1 GB), y `requirements.txt` en `-api`, `-ml` y `-dev`; `requirements.txt`
  sigue instalando todo (verificado en venv nuevo: exit 0, `pip check` limpio,
  27 tests). `xgboost` pasó a `xgboost-cpu==2.1.1` (misma versión y mismo
  `import xgboost`). `api` es la última etapa a propósito: un `docker build .`
  sin target (Railway) construye la API.
- Esqueleto de frontend en `frontend/` (React 19 + Vite 8 + react-leaflet 5, solo
  mapa base y estado de `/health`) con imagen `web` (nginx, reenvía `/api/` a la
  API). **No implementa TASK-027 a 031.**
- En `docker-compose.yml` las variables van explícitas en `environment`: con
  `env_file` + `docker compose run`, el contenedor `ml` solo recibía
  `DATABASE_URL` y faltaba `SECRET_KEY`.
- El job de predicción correrá con la imagen `ml`, no dentro de FastAPI. Sigue
  sin decidir cómo llega el modelo entrenado en Colab al job.
- Quien ya tenía `xgboost` instalado debe hacer `pip uninstall xgboost` antes de
  reinstalar.

**Pendiente**
- **TASK-004, despliegue en la nube (pospuesto por decisión del usuario).** Falta
  elegir proveedor. Railway: crédito de prueba de $5 o plan Hobby de $5/mes; la BD
  debe usar la plantilla PostGIS, no el Postgres por defecto. Alternativas
  gratuitas con PostGIS: API en Render o Northflank + base en Neon (la API de
  Render se duerme tras 15 min; el job semanal TASK-016 tendría que dispararse
  desde un cron externo). Render Postgres gratis caduca a los 30 días: no sirve.
  Si se cambia de proveedor, actualizar ADR-003 y `design.md` §1 y §10.
- Ahora hace falta un `.env` local con `SECRET_KEY` (antes bastaba `DATABASE_URL`).

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

### 2026-10-25 — TASK-017/018 autenticación JWT y RBAC

**Estado:** implementación terminada, tests verdes y `TASK-017`/`TASK-018`
marcadas `[x]` tras confirmación explícita de Ivonne (2026-10-25). Falta
solo que Ivonne revise y haga el commit.

**Implementado**
- `app/core/security.py`: bcrypt (costo 12) y JWT HS256 con access de 30
  min y refresh de 7 días; claims `sub`, `rol`, `tipo`, `jti`, `iat`,
  `exp`, `iss`. El algoritmo está restringido a HS256.
- `app/models/refresh_token.py` + migración `aa12e214cb8d`: tabla
  `refresh_tokens` (`jti` único, usuario, expiración, revocación,
  creación). `RefreshToken` se registró en `app/models/__init__.py` y se
  agregó la relación en `Usuario`.
- `app/api/routes/auth.py`: `POST /auth/login` (OAuth2 password flow),
  `POST /auth/refresh` con rotación y `POST /auth/logout` idempotente.
- `app/api/deps.py`: `get_current_user` carga usuario y rol desde la BD en
  cada request; `require_role(...)` aplica RBAC sin bypass implícito de
  admin.
- `app/schemas/auth.py`: `TokenPair` y `RefreshTokenRequest`.
- `app/main.py`: incluye el router de auth.
- `app/etl/seed_usuarios.py`: seed idempotente de roles y 5 usuarios
  ficticios `@demo.local`; la contraseña sale de `SEED_DEMO_PASSWORD` o se
  pide por consola. Incluye `--delete` y `--reset-passwords`; rechaza
  `ENVIRONMENT=production`.
- `.env.example`: agrega `JWT_ISSUER` y `SEED_DEMO_PASSWORD=` (vacío).
- `README.md`: instrucciones reproducibles de PostGIS local, migraciones,
  seed, limpieza y tests.
- `design.md` §4: documenta `/auth/refresh` y `/auth/logout` además de
  `/auth/login`, para que el contrato de API coincida con la implementación.
- `tests/api/`: 19 pruebas de login, refresh, expiración, token sin
  `exp`, rotación, logout, tipo de token y RBAC 401/403.

**Decisiones**
- El refresh token es revocable mediante `refresh_tokens` (SEG-01). En
  `/auth/refresh` se revoca el token usado y se emite uno nuevo.
- El access token no se persiste; su expiración corta limita el riesgo.
- Se usa `bcrypt` directo, no `passlib`, porque el entorno tiene bcrypt
  5.0 y passlib 1.7.4 no está instalado.
- `decodificar_token` exige `exp` con `options={"require_exp": True}`: un
  token firmado sin expiración ya no se acepta.
- Los usuarios demo no se versionan: solo se versiona el script. Cada
  desarrollador define su propia contraseña local.
- No hay bypass automático de `admin`; cada endpoint declara sus roles.
- El alcance por municipio (`municipio_asignado_id`) es una validación de
  servicio posterior, no parte de `require_role`.

**Verificación**
- `pytest tests/api -q`: **19 passed**.
- `ruff check` sobre los archivos nuevos: **All checks passed**.
- `python -m compileall -q app tests`: OK.
- `alembic upgrade head` y `alembic check`: sin operaciones nuevas.
- Smoke test del seed: login con `epidemiologo@demo.local` devuelve 200
  con access y refresh; luego `--delete` elimina los 5 usuarios demo.
- PostGIS temporal: contenedor `dengue-postgis-local`, puerto `55432`,
  base `dengue_malaria`. Queda levantado para pruebas manuales.

**Pendientes**
- Ivonne debe revisar y commitear; el agente no commitea.
- Se mantiene la extensión aprobada por Ivonne: `/auth/refresh` y
  `/auth/logout` además de `/auth/login`, documentada en `design.md` §4.
- Rate limiting de login (SEG-10) y HTTPS de despliegue siguen fuera de
  alcance de estas dos tareas.
- El access token no es revocable; si se requiere, evaluar una lista de
  revocación o expiración aún más corta.

### 2026-10-26 — TASK-014 pipeline de predicción + SHAP + tabla predicciones

**Estado:** implementación terminada, verificada y `TASK-014` marcada como
`[x]` tras confirmación explícita de Ivonne (2026-10-26).

**Decisiones acordadas para esta sesión**
- Horizonte operativo **t+3**; t+4 queda disponible por parámetro pero no se
  publica en el lote semanal. Motivo: la validación t+4 solo tiene 2 orígenes
  walk-forward y `predicciones` no tiene columna de horizonte; publicar ambos
  crearía filas/alertas duplicadas indistinguibles.
- Cortes provisionales de `nivel_riesgo`: `<33.33` bajo, `33.33-66.67`
  medio, `>=66.67` alto. **No validados** ni equivalentes a brote.
- `nivel_confianza` NFR-007 estricto con los umbrales de TASK-010:
  `<=5 %` alto, `>5 % y <=20 %` bajo, `>20 %` no se publica; `medio` queda
  reservado.
- El modelo puntúa los 28 municipios del panel, pero solo se persisten los 4
  del catálogo piloto. Ampliar el catálogo requiere geometrías oficiales y
  pertenece a la capa de datos, no a TASK-014.

**Implementado**
- `app/ml/prediccion.py`: features → artefacto TASK-012 → SHAP TASK-013,
  cálculo de riesgo/confianza/fecha, persistencia inmutable y CLI.
- `app/models/prediccion.py` + migración `5f6a7b8c9d01`: tabla
  `predicciones` con los CHECK de `design.md` §3, incluido el horizonte de
  21-28 días.
- `tests/ml/test_prediccion.py`: 18 pruebas (cortes, NFR-007, fechas, ORM,
  persistencia simulada y pipeline real con SHAP).
- `docs/task_014_prediccion.md`: decisiones, uso, verificación y limitaciones.

**Verificación**
- `python -B -m unittest discover -s tests/ml -p "test_prediccion.py" -v`:
  **18 OK**.
- Suite `tests/ml`: **66 OK, 3 omitidas** (omisiones previas de pandas 2.2.3;
  SHAP ya quedó disponible en el intérprete global).
- `alembic upgrade head` y `alembic check`: sin operaciones nuevas.
- Inserción real en transacción sobre PostgreSQL/PostGIS: 28 predicciones,
  4 insertadas (piloto), 24 omitidas por catálogo; rollback posterior.
- `ruff check` y `python -m compileall -q app tests`: OK.

**Pendientes**
- Si se quiere publicar t+4, agregar `horizonte_semanas` al esquema y definir
  la regla de selección para `GET /zonas/riesgo` y alertas.
- Integrar el porcentaje real de imputación de TASK-010; mientras el panel v2
  no conserve `es_dato_imputado`, la confianza usa una estimación por
  features climáticas ausentes.
- TASK-015 debe partir de `predicciones.variables_explicativas` y no crear
  alertas sin justificación.

### 2026-10-26 — API de zonas y alertas (TASK-019 a TASK-023, Dilan)

**Estado:** implementado y verificado contra PostgreSQL 17 + PostGIS 3.6
locales (`pytest tests/api tests/test_modelos_predicciones.py`: 133 tests en
verde; `alembic upgrade head`, `downgrade` y `alembic check` sin diferencias).
**Sin commit ni push** de este trabajo. TASK-019 a 022 marcadas `[x]`;
TASK-023 queda sin marcar (ver pendientes).

**Implementado**
- Modelos y migración `7c1e5d9a3b42`: `predicciones`, `alertas`,
  `umbrales_configuracion`, `brotes_confirmados` (nadie las tenía asignadas;
  divergencias anotadas en `design.md` §3 antes de marcar las tareas).
- `app/api/deps.py`: verifica el JWT de acceso y el rol (`get_usuario_actual`,
  `require_role`). No emite tokens (TASK-017) ni toca `roles`/`usuarios`.
- `app/services/` (consultas y reglas por rol), `app/schemas/` y
  `app/api/routes/{zonas,alertas,admin}.py`; `app/main.py` los registra.
- `docs/contrato_api.md`: el "borrador de la API" del día 1 (rutas, payloads y
  claims del token), además de `docs/contrato_esquema_bd.md` ampliado.
- Pruebas en `tests/api/` y `tests/test_modelos_predicciones.py`. El fixture
  `catalogo` pasó a `tests/conftest.py`; ahora `conftest.py` fija `SECRET_KEY`
  solo para pruebas.

**Decisiones que este diseño no fijaba (confirmar con el equipo)**
- Vista completa de predicción: `epidemiologo` y `admin`; `autoridad`, `sedes`
  y `coordinador_municipal` reciben la resumida.
- Umbral por defecto 70 % (referencial, ejemplo de REQ-009).
- Correlación predicción↔brote: ±7 días de `fecha_estimada_riesgo`.
- `app/main.py` ahora importa `app.core.database`, por lo que arrancar la API
  exige `DATABASE_URL` (antes `/health` arrancaba sin ella).

**Pendientes**
1. Ivonne: `/auth/login` debe emitir los claims de `docs/contrato_api.md`;
   `evaluacion_alertas` (TASK-015) debe leer `obtener_umbral` y TASK-014 debe
   insertar en `predicciones` (variables como lista). Seed de `roles`.
2. Quién carga `brotes_confirmados` (sin fuente asignada): sin datos, el
   historial y TASK-034 quedan vacíos.
3. TASK-032: cobertura medida 2026-10-26 sobre `app/etl` + `app/ml`: **86 %**
   total (205 tests en verde; `entrenamiento.py` 75 %, el resto ≥ 84 %).
   Falta `prediccion.py` (TASK-014, Ivonne): al existir, repetir
   `pytest --cov=app/etl --cov=app/ml` y marcar la tarea.
4. TASK-031 y TASK-035 dependen de Adriana (024/025) y del cierre del resto.
5. Entorno: Python 3.12 (`pip install -r requirements.txt` no funciona en
   3.14). No crear el venv dentro de una carpeta sincronizada con iCloud
   (`Documents`): los imports se cuelgan. Se usó `~/.venvs/dengue-malaria` y
   el repo en `~/Pictures/machine/`. Suite completa: ~11 s.

### 2026-10-26 — TASK-024/025: campañas y recomendaciones municipales

**Implementación:** routers `campanas.py` y `municipios.py`, schemas
`prevencion.py` y servicios compartidos `prevencion.py`/`reglas_prevencion.py`.
`app/main.py` registra ambos routers. Se reutilizan JWT/RBAC, catálogos y
predicciones almacenadas; no se modifican modelos, migraciones, ML ni los
endpoints de TASK-019 a 023.

**Reglas:** dengue t+3 verificable por metadatos del modelo, enfermedad y
diferencia de 21 días UTC; fecha objetivo no vencida. Se filtra antes de
elegir la última fila por municipio (fecha e ID). Campañas ordena por riesgo,
fecha, probabilidad e ID municipal. Recursos devuelve recomendaciones
orientativas del MVP, sin inventarios. Coordinadores limitados al municipio
asignado; 403 sin asignación. Administrador solo en recursos, no campañas.

**Evidencia y límites:** `docs/task_024_025_api.md` y
`docs/decisiones_task_024_025.md`. Pruebas locales: 19 aprobadas y 27 de
integración omitidas por dependencias ausentes y falta de BD exclusiva de
pruebas. No se instaló nada ni se escribió en PostgreSQL. TASK-024/025 no
se marcan completas hasta verificar integración HTTP/PostgreSQL/JWT.
