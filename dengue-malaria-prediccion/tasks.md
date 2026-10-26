# Plan de Tareas — Predicción Temprana de Brotes de Dengue/Malaria

**Versión:** 1.0
**Basado en:** `requirements.md` v1.0, `design.md` v1.0

> ▶️ **Estado (2026-10-26):** el MVP corre de punta a punta en local y en Docker
> (datos reales → ingesta → modelo → alertas → API con login por rol → interfaz
> web) y la CI de GitHub está en verde. Hechas 37 de 48 (con la 033): la capa de datos (005 a
> 010), el baseline (012), el motor de predicción, las alertas y la autenticación
> (014, 015, 017, 018), toda la API (019 a 025, 047), las pruebas y la cobertura
> (032), el manejo de errores (040), la vista de campañas (031) y casi toda la
> Fase 7. **Bloquea la defensa:** una fuente de brotes confirmados (el despliegue
> en la nube, TASK-004, ya está resuelto en Render + Neon). Faltan además la tarea
> semanal (016), `/modelo/desempeno` (026), la
> validación retrospectiva (034), la revisión de seguridad (035), las
> limitaciones del informe (036), el tag (041) y el ensayo con el Plan B (045).
> Dengue se predice a 3 semanas; **malaria se muestra con casos observados**
> porque no existe serie semanal (ADR-005).

Cada tarea referencia su(s) REQ/NFR correspondiente en la misma línea del
checkbox, para que sea verificable de forma automática.

---

## Fase 1 — Infraestructura base

*Meta de la fase: tener el proyecto ejecutable localmente y en la nube
(Render + Neon), con base de datos PostGIS lista.*

- [x] **TASK-001** [NFR-005, NFR-008] Inicializar repositorio con estructura
      de carpetas definida en `design.md` §9, configurar entorno virtual y
      `requirements.txt` (fastapi, sqlalchemy, alembic, psycopg2, pydantic,
      python-jose, passlib[bcrypt], scikit-learn, shap, xgboost, pandas).
      *Verificación:* `pip install -r requirements.txt` corre sin errores.
      *Verificado 2026-10-25:* en un venv nuevo, `pip install -r requirements.txt` termina con exit 0 y `pip check` no reporta conflictos. `requirements.txt` ya traía todas las dependencias; no se modificó. Todas tienen wheel para Linux/Python 3.12 (la versión fijada en el `Dockerfile`).

- [x] **TASK-002** [NFR-008] Configurar PostgreSQL local con extensión
      PostGIS habilitada (`CREATE EXTENSION postgis;`).
      *Verificación:* `SELECT PostGIS_Version();` devuelve una versión válida.
      *Verificado 2026-10-25:* `docker compose up -d db` (`docker-compose.yml`, imagen `postgis/postgis:16-3.4`, que habilita PostGIS al crear la base) y `SELECT PostGIS_Version();` devuelve `3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1`. Antes de esta fecha el repositorio no tenía ningún `docker-compose.yml`.

- [x] **TASK-003** [NFR-005] Configurar `app/core/config.py` para leer
      variables de entorno (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
      `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`,
      `ENVIRONMENT`) sin credenciales hardcodeadas.
      *Verificación:* revisión manual — ningún secreto en el código fuente.
      *Verificado 2026-10-25:* `app/core/config.py` (pydantic-settings) lee las 6 variables del entorno o de `.env`; `DATABASE_URL` y `SECRET_KEY` no tienen valor por defecto y, con `ENVIRONMENT=production`, se rechaza una `SECRET_KEY` de ejemplo o de menos de 32 caracteres. `app/core/database.py` y `alembic/env.py` leen de `get_settings()` (antes `os.environ`). `tests/test_config.py` (3 tests); suite completa: 27 tests en verde. Ningún secreto en el código de `app/` ni `alembic/`.

- [x] **TASK-004** [NFR-008] Conectar el proyecto a un proveedor de nube
      (servicio PostgreSQL + servicio FastAPI) y confirmar despliegue de un
      endpoint `/health` de prueba. *Proveedor: Render + Neon, no Railway (ADR-006).*
      *Verificación:* `curl https://<app>/health` responde 200.
      *Verificado 2026-10-26:* `curl https://taller-de-sistemas-inteligentes.onrender.com/health`
      → 200 `{"status":"ok"}` con certificado TLS válido; `http://` redirige con 301 a
      `https://`; `POST /auth/login` con credenciales falsas → 401 en ~2 s, lo que
      confirma que la API consulta la base de Neon (PostgreSQL 16, PostGIS 3.3.10,
      4 migraciones aplicadas, tablas vacías). `/docs` y `/openapi.json` responden.
      *Antes (historial):* el despliegue estuvo pendiente de decisión del 2026-10-25. *Hecho y verificado en local:*
      `Dockerfile` con dos targets (`api` 323 MB, `ml` 2,3 GB; Python 3.12
      fijado), `frontend/Dockerfile` (`web`, 74 MB), `.dockerignore` y
      `docker compose up --build api web` →
      `curl http://localhost:8000/health` = 200 y `curl http://localhost:8080/api/health` = 200.
      *Re-verificado 2026-10-26 en un Mac con Apple Silicon (Colima):* las tres
      imágenes (`api` 355 MB, `ml` 1,16 GB, `web` 76 MB) se construyen; con
      `docker compose` se migra, se carga la demostración y `scripts/smoke_test.py`
      pasa contra `:8000` y contra `:8080/api` (nginx). La suite completa pasa
      también contra PostgreSQL 16 + PostGIS 3.4, la misma versión que usa el CI.
      Esa prueba encontró que la API importaba `pandas` (ausente en la imagen
      `api`); corregido y vigilado por `tests/test_api_ligera.py`.
      El `railway.toml` se eliminó el 2026-10-26 (queda en el historial de Git).
      Las migraciones se aplican al arrancar con `RUN_MIGRATIONS=1` (`CMD` del
      `Dockerfile`; el campo Docker Command de Render debe quedar vacío). Pasos y
      problemas encontrados en `../docs/guia_despliegue_render_neon.md`.
      *Limitaciones conocidas:* la API gratuita se duerme tras 15 min sin tráfico
      (la primera petición tarda cerca de 1 min); Neon gratuito es de ~0,5 GB y
      suspende el cómputo sin uso; la contraseña de Neon se compartió por chat y
      debe rotarse.

---

## Fase 2 — Capa de datos

*Meta de la fase: modelo de datos completo, migraciones aplicadas, y
pipeline de ingesta/limpieza funcionando con datos de prueba.*

- [x] **TASK-005** [REQ-017, REQ-018] Crear modelos ORM y migraciones Alembic
      para `departamentos`, `municipios` (con columna geometría PostGIS) y
      `enfermedades`.
      *Verificación:* `alembic upgrade head` crea las tablas; `\d municipios`
      muestra la columna `geometria` como tipo geometry.
      *Verificado 2026-10-25:* `alembic upgrade head` en PostGIS 3.4 crea las 7 tablas; `\d municipios` muestra `geometria geometry(MultiPolygon,4326)` con índice GIST `idx_municipios_geometria`.

- [x] **TASK-006** [REQ-013, REQ-015] Crear modelos y migraciones para
      `casos_epidemiologicos` y `datos_climaticos`, incluyendo `fuente`,
      `fecha_ingesta` y `es_dato_imputado`.
      *Verificación:* inserción de prueba respeta constraints (`CHECK >= 0`,
      `UNIQUE(municipio_id, fecha)` en clima).
      *Verificado 2026-10-25:* en PostgreSQL real, `casos_confirmados = -1` falla con `ck_casos_no_negativos` y un segundo clima con el mismo `(municipio_id, fecha)` falla con `uq_clima_municipio_fecha`. `fuente`, `fecha_ingesta` y `es_dato_imputado` son NOT NULL.

- [x] **TASK-007** [REQ-019, REQ-020] Crear modelos y migraciones para
      `usuarios` y `roles`, con `password_hash` y sin campos de datos
      personales de pacientes.
      *Verificación:* intento de insertar un usuario con contraseña en texto
      plano falla la revisión de código / test unitario de hashing.
      *Verificado 2026-10-25:* `usuarios` tiene `email`, `password_hash` (NOT NULL), `rol_id` y `municipio_asignado_id`; ningún campo de pacientes. `tests/test_modelo_usuarios.py` fija el esquema. El hashing con bcrypt es TASK-017.

- [x] **TASK-008** [REQ-014] Implementar conector de ingesta para datos
      climáticos públicos. **Fuente ya confirmada:** SENAMHI Bolivia (WIS
      2.0) — ver `docs/eda_inicial.md` §2.2. Existe ya una descarga
      funcional fuera de `app/etl/conectores/` (`scripts/descargar_senamhi.py`);
      esta tarea es adaptar esa lógica al conector formal del backend, no
      reemplazarla ni volver a diseñarla.
      *Verificación:* test que ingiere un CSV/JSON de muestra y valida que
      los registros aparecen en `datos_climaticos` con `fuente` poblada.
      *Verificado 2026-10-25:* `tests/etl/test_senamhi.py` (5 tests) pasa contra PostGIS real.

- [x] **TASK-009** [REQ-014] Implementar conector de ingesta para datos
      epidemiológicos históricos. **Fuente ya confirmada:** Ministerio de
      Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13 — ver
      `docs/eda_inicial.md` §2.1. **Limitación conocida:** la fuente entrega
      acumulados municipales SE1-13, no series semana-a-semana; confirmar si
      esa granularidad mejora antes de dar por cerrada esta tarea (ver
      `docs/cierre_sprint1.md` §3.2).
      *Verificación:* test análogo a TASK-008 para `casos_epidemiologicos`.
      *Verificado 2026-10-25:* **dengue** se ingiere como serie SEMANAL por municipio (`ingerir_dengue_semanal`, `fecha_reporte` = domingo de la semana ISO, `es_dato_imputado = false`); fuente: `data/processed/dengue_municipal_semanal.csv` (28 municipios × 13 semanas, verificada contra los totales del boletín). Solo los municipios del catálogo (zona piloto, 4) se insertan. **Malaria** se guarda como acumulado SE1-13 (3 filas en la zona piloto): no existe serie semanal en ninguna fuente. Decisión registrada en `docs/adr/ADR-005-malaria-acumulado-en-bd.md`; el modelo de malaria entrena con `data/processed/panel_bloques_malaria_clima.csv`. 13 tests en `tests/etl/test_epidemiologia.py`.

- [x] **TASK-010** [REQ-013, NFR-007] Implementar módulo de limpieza e
      imputación (`app/etl/limpieza.py`) siguiendo `docs/reglas_calidad_datos.md`:
      interpolación temporal para climáticos faltantes, marcado de
      `es_dato_imputado`, y cálculo del porcentaje de datos faltantes por
      municipio/ventana. **Nota de Línea Base:** ya existe un prototipo de
      este pipeline probado sobre datos reales (Sprint 1, Línea Base — Paso
      2); antes de empezar esta tarea, confirmar con Tania si ese prototipo
      ya está subido al repositorio para reutilizar su lógica en vez de
      rediseñarla desde cero.
      *Verificación:* test unitario con dataset que tiene 20% de valores
      faltantes; el resultado no contiene NaN y se marca el flag de
      confianza baja cuando corresponde (ver TASK-014).
      *Verificado 2026-10-25:* `tests/etl/test_limpieza.py` (4 tests) pasa, incluido el de 20 % de faltantes sin NaN y con confianza baja.

---

## Fase 3 — Lógica de negocio / motor de predicción

*Meta de la fase: el pipeline de ML genera predicciones explicables y
almacenables, cumpliendo el horizonte de 3-4 semanas.*

- [ ] **TASK-011** [REQ-002] Implementar `app/ml/features.py`: generación de
      variables rezagadas (lag 2-4 semanas) y promedios móviles a partir de
      `casos_epidemiologicos` y `datos_climaticos`.
      *Verificación:* test unitario valida que las columnas de lag se
      calculan correctamente sobre una serie de tiempo de ejemplo.

- [x] **TASK-012** [NFR-001, NFR-002] Entrenar modelo baseline (offline, en
      notebook/Colab) usando XGBoost u otro clasificador, con datos
      disponibles o sintéticos representativos; documentar métricas
      obtenidas (aclarando que son estimadas hasta validarse con datos
      reales del piloto).
      *Verificación:* métricas de validación cruzada registradas en
      `modelos.metricas_entrenamiento` (JSONB) y documentadas en el reporte
      del proyecto.

- [ ] **TASK-013** [REQ-004] Implementar `app/ml/explicabilidad.py` usando
      SHAP para calcular la importancia de variables por predicción
      individual.
      *Verificación:* test que, dado un input de ejemplo, retorna una lista
      ordenada de variables con peso numérico.

- [x] **TASK-014** [REQ-001, REQ-002, REQ-003, NFR-007] Implementar
      `app/ml/prediccion.py`: ejecuta el pipeline completo (features →
      modelo → SHAP), calcula `nivel_riesgo`, `probabilidad_pct`,
      `nivel_confianza` (bajo si el % de datos imputados supera el umbral de
      NFR-007) y `fecha_estimada_riesgo` (fecha_generacion + 21 a 28 días).
      *Verificación:* test de integración genera una predicción completa y
      la valida contra las restricciones de `design.md` §3 (tabla
      `predicciones`).

- [x] **TASK-015** [REQ-005, REQ-009, REQ-010] Implementar
      `app/ml/evaluacion_alertas.py`: compara `probabilidad_pct` contra
      `umbrales_configuracion`; si se supera el umbral **y** existen
      variables explicativas, crea fila en `alertas`; si no hay
      justificación, no se crea la alerta y se registra en log.
      *Verificación:* test unitario con probabilidad alta pero sin variables
      explicativas confirma que NO se genera alerta.
      *Verificado 2026-10-26:* `app/ml/evaluacion_alertas.py` implementa `evaluar_prediccion`, `evaluar_alertas_lote`, `evaluar_alertas_pendientes` y CLI. `tests/ml/test_evaluacion_alertas.py` (12 tests) pasa al 100%: confirma REQ-005 (probabilidad alta sin explicabilidad no genera alerta y registra log warning), REQ-009 (probabilidad >= umbral genera alerta), REQ-010 (cambio de umbral con `configurar_umbral` en caliente se refleja de inmediato sin reinicio) y jerarquía departamental vs general.

- [ ] **TASK-016** Configurar tarea programada (APScheduler o cron de
      Railway) para ejecutar el pipeline de predicción semanalmente.
      *Verificación:* ejecución manual del job confirma inserción de nuevas
      filas en `predicciones` con fecha correcta.

---

## Fase 4 — Capa de API

*Meta de la fase: exponer toda la funcionalidad vía API REST segura y con
control de acceso por rol.*

- [x] **TASK-017** [REQ-019] Implementar `/auth/login` con JWT (access +
      refresh token) y hashing de contraseñas con bcrypt.
      *Verificación:* test de integración: login con credenciales válidas
      devuelve token; con credenciales inválidas devuelve 401.

- [x] **TASK-018** [REQ-007, REQ-019] Implementar dependencias de RBAC en
      `app/api/deps.py` (`require_role(...)`) para restringir endpoints
      según rol.
      *Verificación:* test que un usuario con rol "autoridad" recibe 403 al
      llamar un endpoint restringido a "epidemiologo".

- [x] **TASK-019** [REQ-001, REQ-006] Implementar `GET /zonas/riesgo`
      (listado de zonas con nivel de riesgo actual, para mapa de calor).
      *Verificación:* test de integración devuelve lista con `nivel_riesgo`
      y coordenadas/geometría para cada municipio.
      *Verificado 2026-10-26:* `tests/api/test_zonas_riesgo.py` (10 tests) pasa contra PostGIS real: cada zona trae `nivel_riesgo`, geometría GeoJSON y centroide; usa la última predicción por zona y enfermedad. Con 350 municipios la consulta respondió con p95 de 22 ms en un chequeo local puntual, sin HTTP ni polígonos realistas (no sustituye a TASK-033, que midió 423 ms con 1 usuario).

- [x] **TASK-020** [REQ-002, REQ-003, REQ-004, REQ-007] Implementar
      `GET /zonas/{id}/prediccion`, devolviendo campos completos para roles
      técnicos y campos resumidos para roles de autoridad.
      *Verificación:* test compara la respuesta para dos roles distintos y
      confirma la diferencia de campos expuestos.
      *Verificado 2026-10-26:* `tests/api/test_zona_prediccion.py` pasa: `epidemiologo`/`admin` reciben `vista: completa` con variables explicativas y modelo; el resto, `vista: resumida` sin esos campos (ni en null).

- [x] **TASK-021** [REQ-008] Implementar `GET /zonas/{id}/historial`
      (predicciones pasadas + brotes confirmados de `brotes_confirmados`).
      *Verificación:* test de integración con datos de ejemplo devuelve
      ambos conjuntos correlacionados por fecha.
      *Verificado 2026-10-26:* `tests/api/test_historial.py` pasa: predicciones (cronológicas) y brotes correlacionados con ventana de ±7 días y `anticipacion_dias`; solo `epidemiologo`/`admin`. La regla de correlación es referencial (ver `docs/contrato_api.md`).

- [x] **TASK-022** [REQ-009] Implementar `GET /alertas` con filtros por
      zona/fecha/enfermedad.
      *Verificación:* test de integración filtra correctamente por
      parámetros de consulta.
      *Verificado 2026-10-26:* `tests/api/test_alertas.py` pasa: filtros por zona, enfermedad y fechas, paginación; no publica alertas cuya predicción no tenga variables explicativas.

- [x] **TASK-023** [REQ-010] Implementar `POST /admin/umbrales` (solo rol
      admin) para configurar umbrales por enfermedad/departamento.
      *Verificación:* test confirma que el cambio se refleja en la siguiente
      llamada a `evaluacion_alertas` (TASK-015).
      *Verificado 2026-10-26:* `app.services.umbrales.obtener_umbral` es consumido directamente por `app/ml/evaluacion_alertas.py` (TASK-015). Verificado en `tests/ml/test_evaluacion_alertas.py::test_req010_cambio_dinamico_de_umbral` y `tests/api/test_admin_umbrales.py`.

- [x] **TASK-024** [REQ-011] Implementar `GET /campanas/priorizacion`
      (zonas ordenadas por riesgo y proximidad de fecha estimada).
      *Verificación:* test de integración valida el orden esperado dado un
      conjunto de predicciones de ejemplo.
      *Verificado 2026-10-26:* implementada por Adriana (`app/api/routes/campanas.py`, `app/services/prevencion.py`). Ella dejó sus 27 pruebas de integración omitidas por no tener una base de pruebas; se corrieron contra PostgreSQL 16 real con JWT: **46 de 46 pasan** (`tests/prevencion/`, con `GATOBYTE_TEST_DATABASE_URL`), y el CI ya las ejecuta. Con las predicciones reales del pipeline, SEDES ve los 4 municipios ordenados, la coordinación solo el suyo y el admin recibe 403 (`tests/e2e/test_flujo_completo.py`). Las reglas son provisionales y así lo dice la respuesta (`docs/task_024_025_api.md`).

- [x] **TASK-025** [REQ-012] Implementar `GET /municipios/{id}/recursos`
      (recomendación de nivel de atención según riesgo vigente).
      *Verificación:* test de integración devuelve recomendación coherente
      con el nivel de riesgo almacenado.
      *Verificado 2026-10-26:* igual que la TASK-024: 46 pruebas de integración en verde contra PostgreSQL; la coordinación solo ve su municipio (403 en otro), el admin ve cualquiera, y la recomendación es coherente con el nivel de riesgo almacenado. Son recomendaciones orientativas, no inventarios ni protocolos oficiales.

- [ ] **TASK-026** [REQ-016] Implementar `GET /modelo/desempeno` (métricas
      de precisión espacial y anticipación calculadas sobre un periodo).
      *Verificación:* test con datos de ejemplo de predicciones y brotes
      confirmados calcula correctamente precisión espacial.

---

## Fase 5 — Dashboard (frontend)

*Meta de la fase: interfaz funcional diferenciada por rol, con mapas de
calor navegables.*

- [x] **TASK-027** [REQ-006] Implementar vista de mapa de calor
      (React + Leaflet/Mapbox) consumiendo `GET /zonas/riesgo`, con
      selector de nivel de agregación (zona/municipio/departamento).
      *Verificación:* prueba manual — el mapa cambia de color según nivel de
      riesgo y responde al cambio de agregación.
      *Verificado 2026-10-26:* mapa navegable con Leaflet (`MapaZonas.jsx`) que consume `GET /zonas/riesgo` (dengue) y `GET /casos/resumen` (malaria), con selector **Municipio / Departamento** (`VistaMapa.jsx`, `agregacion.js`). En el modelo de datos la «zona» es el municipio (design.md §3), por eso hay dos niveles. Por departamento se muestra el mayor riesgo y la mayor probabilidad entre sus municipios (criterio de peor caso, solo de visualización: no es una predicción nueva) y, en malaria, la suma de casos. Prueba manual en el navegador contra el sistema en Docker: el mapa cambia de color según el riesgo (dengue: Beni y La Paz en riesgo medio) y responde al cambio de agregación (malaria: Beni 293 y La Paz 157, 450 en total). 120 pruebas de interfaz en verde.

- [x] **TASK-028** [REQ-007] Implementar vista simplificada para autoridades
      (indicadores generales, zonas críticas) y vista detallada para
      epidemiólogos/equipos técnicos (variables, confianza, historial).
      *Verificación:* prueba manual con dos usuarios de rol distinto
      confirma diferencias de UI acorde a REQ-007.
      *Verificado 2026-10-26:* prueba manual en el navegador con `autoridad@demo.local` y `epidemiologo@demo.local`: la autoridad recibe la vista resumida (probabilidad y confianza) y ve la invitación a pedir el detalle técnico; el epidemiólogo ve además «Qué influyó en esta predicción» (variables SHAP) y la pestaña Historial. La diferencia sale del servidor (`vista: resumida | completa`), no de la interfaz. Cubierto por `frontend/src/test/App.test.jsx`.

- [ ] **TASK-029** [REQ-008] Implementar vista de historial de predicciones
      vs. brotes confirmados, con filtro por zona y fecha.
      *Verificación:* prueba manual sobre datos de ejemplo cargados en
      Fase 2.
      *Estado 2026-10-26 (sin marcar):* existe la vista de historial para técnicos (`Historial.jsx`) con predicciones, brote confirmado y la regla de comparación. **Faltan el filtro por rango de fechas en pantalla** (la API ya lo soporta) **y datos de brotes confirmados** (sin fuente, riesgo M-08), así que hoy ninguna predicción aparece como acertada.

- [x] **TASK-030** [REQ-009] Implementar panel de alertas activas con
      justificación visible (variables explicativas).
      *Verificación:* prueba manual — cada alerta mostrada incluye al menos
      una variable explicativa (nunca una alerta "vacía").
      *Verificado 2026-10-26:* prueba manual en el navegador contra el sistema en Docker: con el umbral de dengue bajado a 40 % (`POST /admin/umbrales`) y `python -m app.ml.evaluacion_alertas` (TASK-015), el panel muestra las dos alertas reales (Guayaramerín 44 % e Ixiamas 43 %), cada una con su justificación y las variables que la explican (nunca una alerta vacía). Sin alertas muestra el estado vacío. Cubierto también por `frontend/src/test/App.test.jsx` y `tests/e2e/test_flujo_completo.py`.

- [x] **TASK-031** [REQ-011, REQ-012] Implementar vista de priorización de
      campañas de fumigación y recomendación de recursos por municipio.
      *Verificación:* prueba manual con coordinador municipal de ejemplo.
      *Estado 2026-10-26:* sin avance. Necesita los endpoints de TASK-024 y 025, que no existen.
      *Verificado 2026-10-26:* pestaña «Campañas» (`frontend/src/components/Campanas.jsx`) para SEDES y coordinación municipal. Prueba manual en el navegador con `coordinador@demo.local` contra el sistema en Docker: ve su municipio (Guayaramerín, 44 %, riesgo medio) con sus recomendaciones y la advertencia de reglas provisionales. SEDES ve el orden de todos los municipios sin recomendaciones. 120 pruebas de interfaz en verde.

---

## Fase 6 — Pruebas y validación

*Meta de la fase: confirmar que el sistema cumple los NFR críticos antes de
considerarse listo para el piloto.*

- [x] **TASK-032** [NFR-010] Escribir pruebas unitarias para módulos de
      ingesta, limpieza y predicción, alcanzando cobertura mínima del 70%
      en esos módulos.
      *Verificación:* `pytest --cov=app/etl --cov=app/ml` reporta ≥ 70%.
      *Avance 2026-10-26 (sin marcar):* `pytest --cov=app/etl --cov=app/ml` da 86 % sobre los módulos actuales (205 tests). Falta `app/ml/prediccion.py` (TASK-014, Ivonne); se marca `[x]` cuando exista y siga ≥ 70 %.
      *Verificado 2026-10-26:* `pytest --cov=app/etl --cov=app/ml` da **80 %** (389 tests) con `app/ml/prediccion.py` ya incluido: ingesta 87-94 %, limpieza 91 %, predicción 74 %, entrenamiento 80 %, explicabilidad 91 %. El mínimo de 70 % se exige en CI (`--cov-fail-under=70`). `seed_demo.py` y `seed_usuarios.py` (utilidades de carga) quedan en 62-65 %, fuera de los módulos que pide la tarea.

- [x] **TASK-033** [NFR-004] Realizar prueba de carga básica sobre
      `GET /zonas/riesgo` con un dataset simulado de hasta 350 municipios.
      *Verificación:* p95 de latencia < 2 segundos en el entorno de prueba.
      *Verificado 2026-10-26 (aceptado con 1 a 5 usuarios simultáneos):*
      `scripts/prueba_carga_zonas_riesgo.py` crea una base temporal local (se
      borra al terminar; se niega a correr contra hosts no locales), carga 350
      municipios simulados con polígonos de ~300 vértices y 8 semanas de
      predicciones (700 filas vigentes) y mide con un solo worker de uvicorn.
      Resultados (p95, 0 errores): 1 usuario **423 ms**; 5 concurrentes
      **1 775 ms** (cumple, < 2 s); 10 concurrentes **4 229 ms** y 25
      concurrentes **11 627 ms** (no cumplen).
      **LIMITACIÓN ACEPTADA (decisión del usuario, 2026-10-26):** el criterio se
      da por cumplido para 1 a 5 usuarios simultáneos, que es la carga prevista
      de un dashboard institucional pequeño; con 10 o más usuarios al mismo
      tiempo el p95 supera los 2 s. Causas observadas: la respuesta pesa 5,1 MB
      (cada zona lleva su polígono completo) y el servidor atiende unas 3
      peticiones por segundo sin importar la concurrencia (límite de CPU,
      inferido, no perfilado). **Los datos son simulados y la medición es de la
      máquina local, no de Render** (plan gratuito de 0,1 CPU y Neon con
      arranque en frío: se espera peor). La cifra de 22 ms de TASK-019 fue un
      chequeo puntual sin HTTP ni polígonos realistas y no es comparable.
      *Si hiciera falta más:* simplificar los polígonos, devolver la geometría
      aparte o comprimir la respuesta; cambiaría el contrato de la API.

- [ ] **TASK-034** [NFR-001, NFR-002] Ejecutar validación retrospectiva del
      modelo contra `brotes_confirmados` de la zona piloto (histórico
      disponible) para estimar precisión espacial y anticipación real.
      *Verificación:* reporte documentado con las métricas obtenidas,
      aclarando que son resultados del piloto, no garantías generales.

- [ ] **TASK-035** [REQ-005, REQ-020] Revisión de seguridad y cumplimiento:
      confirmar ausencia de datos personales de pacientes, verificar HTTPS
      en despliegue, y confirmar que no existen alertas sin justificación en
      la base de datos.
      *Verificación:* checklist de revisión firmado por el equipo antes de
      la presentación del proyecto.
      *Estado 2026-10-26 (sin marcar):* `docs/revision_seguridad.md` y `python -m app.core.revision_seguridad` (6 controles OK: sin datos personales, alertas con justificación, hashes bcrypt, predicciones inmutables, `SECRET_KEY`, sin secretos en el repositorio; 44 pruebas que verifican que cada control detecta lo que debe). **HTTPS verificado en Render:** certificado válido, sin `Strict-Transport-Security` (aviso). **Falta la firma del equipo** y decidir los hallazgos: `python-multipart` y `python-jose` con avisos (H-1, H-2), sin límite de intentos de login (H-3), nginx sin cabeceras (H-4). La revisión también detectó que la API desplegada no podía conectarse a Neon por el parámetro `options` de TASK-040; corregido.

- [ ] **TASK-036** Documentar en el informe final del proyecto universitario
      las limitaciones conocidas (sesgo de vigilancia, retraso de reporte,
      cobertura climática irregular) y cómo el sistema las mitiga
      parcialmente.
      *Verificación:* sección de limitaciones presente en el informe final.

---

## Fase 7 — Integración y defensa del MVP

*Meta de la fase: cerrar lo que la "Guía de Defensa del MVP" exige y que las
fases 1-6 no cubrían: sistema integrado y desplegado, flujo extremo a extremo
demostrable, evidencia reproducible y trazabilidad. Estas tareas se agregaron
el 2026-10-26 tras contrastar la guía con el repositorio; la "persona
sugerida" es solo una propuesta, el equipo puede repartirlas distinto.*

- [x] **TASK-037** [REQ-019] Login y sesión en el frontend: pantalla de acceso
      contra `/auth/login`, token en memoria, refresco con `/auth/refresh`,
      cierre de sesión con `/auth/logout` y manejo de 401/403. Sin esto las
      vistas de las TASK-027 a 031 no pueden pedir datos (la API exige JWT).
      *Persona sugerida:* Tania o Ignacio. *Depende de:* TASK-017 (hecha).
      *Verificación:* prueba manual con dos roles; `npm run build` sin errores.
      *Verificado 2026-10-26:* `frontend/src/components/Acceso.jsx` y `src/api.js`. Prueba manual en el navegador con `epidemiologo@demo.local` y `autoridad@demo.local` (cada una ve su vista), y recarga de la página sin pedir contraseña de nuevo. 120 pruebas de interfaz en verde (login, refresco único ante 401, sesión vencida, tiempo máximo, cierre de sesión) y `npm run build` sin errores. Decisión: access token en memoria y refresh token en `sessionStorage` (riesgo M-11).

- [x] **TASK-038** [REQ-001, REQ-002, REQ-013] Datos de demostración
      reproducibles con un solo comando: registra el modelo en `modelos`,
      genera predicciones con `app/ml/prediccion.py` y las persiste, y carga
      usuarios demo. Todo lo que no provenga de una fuente real queda marcado
      como demo (CLAUDE.md regla 1).
      *Persona sugerida:* Dilan con Ivonne. *Depende de:* TASK-014 (hecha);
      alertas demo esperan TASK-015; brotes esperan la decisión de fuente.
      *Verificación:* base vacía → un comando → `GET /zonas/riesgo` devuelve
      zonas con predicción.
      *Verificado 2026-10-26:* `python -m app.etl.seed_demo` sobre una base migrada crea 5 usuarios, ingiere 52 filas semanales de dengue y 3 de malaria del boletín, registra el modelo y persiste 4 predicciones (una por municipio piloto); `GET /zonas/riesgo` las devuelve (`tests/etl/test_seed_demo.py`). Es idempotente (`--forzar` agrega otra tanda). **No** carga predicciones de malaria (sin modelo), brotes ni alertas (sin fuente; TASK-015).

- [x] **TASK-039** [NFR-010] Prueba extremo a extremo del backend (login →
      predicción persistida → `/zonas/riesgo` → `/zonas/{id}/prediccion` con
      dos roles) y script de humo para el despliegue (`/health`, login y
      consulta con curl).
      *Persona sugerida:* Dilan. *Depende de:* TASK-038.
      *Verificación:* `pytest tests/e2e` en verde; el script de humo sale con
      código 0 contra una URL.
      *Verificado 2026-10-26:* `tests/e2e/test_flujo_completo.py` recorre boletín → ingesta → modelo → login → API con dos roles, y la base caída; `scripts/smoke_test.py` pasa contra un servidor real (`tests/e2e/test_smoke_script.py`) y contra la API local. Pendiente repetirlo contra la URL pública cuando exista el despliegue (TASK-004).

- [x] **TASK-040** [NFR-003] Manejo de errores y diagnóstico: logs con
      identificador de petición, respuesta uniforme ante errores no previstos
      (sin filtrar trazas), timeouts de conexión a la base y `/health/ready`
      que responda 503 si la base no responde.
      *Persona sugerida:* Dilan. *Verificación:* tests con la base caída y con
      entrada inválida; los logs muestran el error sin datos sensibles.
      *Verificado 2026-10-26:* `tests/test_observabilidad.py` (12 tests): `/health/ready` responde 503 con la base caída, una consulta lenta se corta y responde 503, el error no previsto responde 500 genérico con la traza solo en el log, el 422 no devuelve lo enviado, y los logs no contienen contraseñas ni correos. Comprobado también en vivo con una API apuntando a un puerto vacío.

- [ ] **TASK-041** Congelar la versión de defensa y la trazabilidad: tag
      `v0.2-mvp`, PR con títulos descriptivos, issues etiquetados con el
      backlog de estabilización y sus responsables.
      *Persona sugerida:* todo el equipo, al final. *Depende de:* TASK-004 y
      las demás de esta fase. *Verificación:* tag y PR visibles en GitHub.
      *Estado 2026-10-26:* pendiente hasta cerrar la fase. PR #28 ya incorporó el primer merge de `dilan`; falta el tag y los issues del backlog de estabilización (no existe ningún issue en el repositorio).

- [x] **TASK-042** Arquitectura vigente: actualizar los diagramas C4,
      `design.md` y el README con lo realmente implementado (contenedores
      Docker, frontend, despliegue), distinguiendo código, configuración y
      secretos. *Persona sugerida:* Tania.
      *Verificación:* cada caja del diagrama tiene su código en el repo.
      *Verificado 2026-10-26:* `docs/arquitectura_actual.md` (diagrama de lo que existe, código por pieza, código vs configuración vs secretos y diferencias con `design.md`); `docs/c4/README.md` lo enlaza. Los SVG C4 del Sprint 1 se conservan como diseño objetivo.

- [x] **TASK-043** Registro de riesgos y limitaciones al estado del MVP: el
      modelo no supera la regla simple en t+3, malaria solo tiene acumulados,
      geometría referencial, 13 semanas de historia, datos provisionales,
      brotes confirmados sin fuente. *Persona sugerida:* Adriana (con
      TASK-036). *Verificación:* `docs/risk_register.md` actualizado.
      *Verificado 2026-10-26:* `docs/risk_register.md`, sección «Actualización al estado del MVP» (14 riesgos y límites reales, M-01 a M-14).

- [x] **TASK-044** [NFR-001, NFR-002] Resumen de resultados experimentales
      contra la línea base, incluidos los intentos fallidos (Experimento C),
      en un solo documento para la defensa. *Persona sugerida:* Ivonne o
      Adriana. *Verificación:* tabla modelo vs baseline con enlaces a los
      artefactos.
      *Verificado 2026-10-26:* `docs/resultados_experimentales.md`: tablas t+3 y t+4 contra la clase mayoritaria y la regla de casos recientes, experimentos A a D con el sobreajuste del C, y la razón de que malaria no tenga modelo.

- [ ] **TASK-045** Guion de demostración y Plan B: pasos de la demo en vivo,
      grabación real de una ejecución y base precargada de respaldo, sin
      maquillar resultados. *Persona sugerida:* todo el equipo.
      *Depende de:* TASK-038/039. *Verificación:* ensayo completo cronometrado.
      *Estado 2026-10-26 (sin marcar):* `docs/guion_demo_y_plan_b.md` listo y sus pasos verificados en local (arranque desde cero, humo, errores en vivo). **Falta el ensayo cronometrado del equipo, la grabación real de una ejecución y el respaldo de base** (se preparan con el sistema final).

- [x] **TASK-046** [NFR-010] Integración continua: GitHub Actions que ejecute
      `pytest` (con PostGIS) en cada PR. *Persona sugerida:* Ignacio.
      *Verificación:* check verde en un PR.
      *Verificado 2026-10-26:* `.github/workflows/ci.yml` se ejecutó en GitHub al subir `dilan` (run 40277147552): **Interfaz (vitest + build) en verde en 15 s y Backend (pytest + PostGIS 3.4) en verde en 2 min 48 s**, con migraciones, `alembic check` y cobertura mínima de 70 %. Aviso de GitHub (no falla): `actions/checkout@v4` y `setup-node@v4` usan Node 20, en retirada.

- [x] **TASK-047** [REQ-008, REQ-014] `GET /casos/resumen`: casos observados
      por municipio y enfermedad (total, rango de fechas, granularidad y
      fuente), todos los roles. Permite mostrar la malaria, que solo tiene
      acumulados SE1-13 (ADR-005) y para la que no hay modelo de predicción.
      *Persona sugerida:* Dilan. *Verificación:* test de integración con
      casos de dengue semanales y de malaria acumulados.
      *Verificado 2026-10-26:* `tests/api/test_casos_resumen.py` (13 tests): dengue semanal y malaria acumulada, geometría para el mapa, filtro, y que nunca suma semanales con acumuladas.

- [x] **TASK-048** [REQ-006, REQ-007] Sistema de diseño del frontend (estilo
      Apple: tipografía del sistema, modo claro y oscuro, escala de espacios,
      materiales translúcidos, movimiento con `prefers-reduced-motion`),
      orientado a la malaria como enfermedad de entrada. Base visual de las
      TASK-027, 028, 030 y 037. *Persona sugerida:* Dilan.
      *Verificación:* contraste ≥ 4,5:1, objetivos táctiles ≥ 44 px y modo
      oscuro revisados en el navegador.
      *Verificado 2026-10-26:* `frontend/src/styles/tokens.css` (fuente del sistema, claro y oscuro, ritmo de espacios, materiales translúcidos, `prefers-reduced-motion/transparency/contrast`). `src/test/contraste.test.js` comprueba 45 pares de color a 4,5:1 en claro y oscuro (detectó que el azul de enlace `#0071e3` solo daba 4,3:1 y se añadió `--enlace`). Revisado en el navegador en escritorio, 390 px y modo oscuro; los 11 controles interactivos miden al menos 44 px.

---

## Notas de alcance

- Las tareas de Fase 5 (dashboard) pueden simplificarse a una interfaz
  mínima si el tiempo del proyecto universitario es limitado, priorizando
  siempre Fases 1-4 (backend, datos y predicción), que son el núcleo técnico
  evaluable del sistema.
- Las preguntas abiertas de `design.md` §10 (fuente de datos climáticos,
  fuente epidemiológica, zona piloto exacta) deben resolverse **antes** de
  TASK-008 y TASK-009 para evitar retrabajo.
