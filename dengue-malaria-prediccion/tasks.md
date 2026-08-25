# Plan de Tareas — Predicción Temprana de Brotes de Dengue/Malaria

**Versión:** 1.0
**Basado en:** `requirements.md` v1.0, `design.md` v1.0

Cada tarea referencia su(s) REQ/NFR correspondiente en la misma línea del
checkbox, para que sea verificable de forma automática.

---

## Fase 1 — Infraestructura base

*Meta de la fase: tener el proyecto ejecutable localmente y en Railway, con
base de datos PostGIS lista.*

- [ ] **TASK-001** [NFR-005, NFR-008] Inicializar repositorio con estructura
      de carpetas definida en `design.md` §9, configurar entorno virtual y
      `requirements.txt` (fastapi, sqlalchemy, alembic, psycopg2, pydantic,
      python-jose, passlib[bcrypt], scikit-learn, shap, xgboost, pandas).
      *Verificación:* `pip install -r requirements.txt` corre sin errores.

- [ ] **TASK-002** [NFR-008] Configurar PostgreSQL local con extensión
      PostGIS habilitada (`CREATE EXTENSION postgis;`).
      *Verificación:* `SELECT PostGIS_Version();` devuelve una versión válida.

- [ ] **TASK-003** [NFR-005] Configurar `app/core/config.py` para leer
      variables de entorno (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
      `ACCESS_TOKEN_EXPIRE_MINUTES`) sin credenciales hardcodeadas.
      *Verificación:* revisión manual — ningún secreto en el código fuente.

- [ ] **TASK-004** [NFR-008] Conectar el proyecto a Railway (servicio
      PostgreSQL + servicio FastAPI) y confirmar despliegue de un endpoint
      `/health` de prueba.
      *Verificación:* `curl https://<app>.up.railway.app/health` responde 200.

---

## Fase 2 — Capa de datos

*Meta de la fase: modelo de datos completo, migraciones aplicadas, y
pipeline de ingesta/limpieza funcionando con datos de prueba.*

- [ ] **TASK-005** [REQ-017, REQ-018] Crear modelos ORM y migraciones Alembic
      para `departamentos`, `municipios` (con columna geometría PostGIS) y
      `enfermedades`.
      *Verificación:* `alembic upgrade head` crea las tablas; `\d municipios`
      muestra la columna `geometria` como tipo geometry.

- [ ] **TASK-006** [REQ-013, REQ-015] Crear modelos y migraciones para
      `casos_epidemiologicos` y `datos_climaticos`, incluyendo `fuente`,
      `fecha_ingesta` y `es_dato_imputado`.
      *Verificación:* inserción de prueba respeta constraints (`CHECK >= 0`,
      `UNIQUE(municipio_id, fecha)` en clima).

- [ ] **TASK-007** [REQ-019, REQ-020] Crear modelos y migraciones para
      `usuarios` y `roles`, con `password_hash` y sin campos de datos
      personales de pacientes.
      *Verificación:* intento de insertar un usuario con contraseña en texto
      plano falla la revisión de código / test unitario de hashing.

- [ ] **TASK-008** [REQ-014] Implementar conector de ingesta para datos
      climáticos públicos (fuente a definir según pregunta abierta en
      `design.md` §10; usar datos de ejemplo/sintéticos si no hay acceso
      confirmado aún).
      *Verificación:* test que ingiere un CSV/JSON de muestra y valida que
      los registros aparecen en `datos_climaticos` con `fuente` poblada.

- [ ] **TASK-009** [REQ-014] Implementar conector de ingesta para datos
      epidemiológicos históricos (fuente a definir; usar datos
      sintéticos/anonimizados de ejemplo si no hay dataset real disponible
      para el proyecto universitario).
      *Verificación:* test análogo a TASK-008 para `casos_epidemiologicos`.

- [ ] **TASK-010** [REQ-013, NFR-007] Implementar módulo de limpieza e
      imputación (`app/etl/limpieza.py`): interpolación temporal para
      climáticos faltantes, marcado de `es_dato_imputado`, y cálculo del
      porcentaje de datos faltantes por municipio/ventana.
      *Verificación:* test unitario con dataset que tiene 20% de valores
      faltantes; el resultado no contiene NaN y se marca el flag de
      confianza baja cuando corresponde (ver TASK-014).

---

## Fase 3 — Lógica de negocio / motor de predicción

*Meta de la fase: el pipeline de ML genera predicciones explicables y
almacenables, cumpliendo el horizonte de 3-4 semanas.*

- [ ] **TASK-011** [REQ-002] Implementar `app/ml/features.py`: generación de
      variables rezagadas (lag 2-4 semanas) y promedios móviles a partir de
      `casos_epidemiologicos` y `datos_climaticos`.
      *Verificación:* test unitario valida que las columnas de lag se
      calculan correctamente sobre una serie de tiempo de ejemplo.

- [ ] **TASK-012** [NFR-001, NFR-002] Entrenar modelo baseline (offline, en
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

- [ ] **TASK-014** [REQ-001, REQ-002, REQ-003, NFR-007] Implementar
      `app/ml/prediccion.py`: ejecuta el pipeline completo (features →
      modelo → SHAP), calcula `nivel_riesgo`, `probabilidad_pct`,
      `nivel_confianza` (bajo si el % de datos imputados supera el umbral de
      NFR-007) y `fecha_estimada_riesgo` (fecha_generacion + 21 a 28 días).
      *Verificación:* test de integración genera una predicción completa y
      la valida contra las restricciones de `design.md` §3 (tabla
      `predicciones`).

- [ ] **TASK-015** [REQ-005, REQ-009, REQ-010] Implementar
      `app/ml/evaluacion_alertas.py`: compara `probabilidad_pct` contra
      `umbrales_configuracion`; si se supera el umbral **y** existen
      variables explicativas, crea fila en `alertas`; si no hay
      justificación, no se crea la alerta y se registra en log.
      *Verificación:* test unitario con probabilidad alta pero sin variables
      explicativas confirma que NO se genera alerta.

- [ ] **TASK-016** Configurar tarea programada (APScheduler o cron de
      Railway) para ejecutar el pipeline de predicción semanalmente.
      *Verificación:* ejecución manual del job confirma inserción de nuevas
      filas en `predicciones` con fecha correcta.

---

## Fase 4 — Capa de API

*Meta de la fase: exponer toda la funcionalidad vía API REST segura y con
control de acceso por rol.*

- [ ] **TASK-017** [REQ-019] Implementar `/auth/login` con JWT (access +
      refresh token) y hashing de contraseñas con bcrypt.
      *Verificación:* test de integración: login con credenciales válidas
      devuelve token; con credenciales inválidas devuelve 401.

- [ ] **TASK-018** [REQ-007, REQ-019] Implementar dependencias de RBAC en
      `app/api/deps.py` (`require_role(...)`) para restringir endpoints
      según rol.
      *Verificación:* test que un usuario con rol "autoridad" recibe 403 al
      llamar un endpoint restringido a "epidemiologo".

- [ ] **TASK-019** [REQ-001, REQ-006] Implementar `GET /zonas/riesgo`
      (listado de zonas con nivel de riesgo actual, para mapa de calor).
      *Verificación:* test de integración devuelve lista con `nivel_riesgo`
      y coordenadas/geometría para cada municipio.

- [ ] **TASK-020** [REQ-002, REQ-003, REQ-004, REQ-007] Implementar
      `GET /zonas/{id}/prediccion`, devolviendo campos completos para roles
      técnicos y campos resumidos para roles de autoridad.
      *Verificación:* test compara la respuesta para dos roles distintos y
      confirma la diferencia de campos expuestos.

- [ ] **TASK-021** [REQ-008] Implementar `GET /zonas/{id}/historial`
      (predicciones pasadas + brotes confirmados de `brotes_confirmados`).
      *Verificación:* test de integración con datos de ejemplo devuelve
      ambos conjuntos correlacionados por fecha.

- [ ] **TASK-022** [REQ-009] Implementar `GET /alertas` con filtros por
      zona/fecha/enfermedad.
      *Verificación:* test de integración filtra correctamente por
      parámetros de consulta.

- [ ] **TASK-023** [REQ-010] Implementar `POST /admin/umbrales` (solo rol
      admin) para configurar umbrales por enfermedad/departamento.
      *Verificación:* test confirma que el cambio se refleja en la siguiente
      llamada a `evaluacion_alertas` (TASK-015).

- [ ] **TASK-024** [REQ-011] Implementar `GET /campanas/priorizacion`
      (zonas ordenadas por riesgo y proximidad de fecha estimada).
      *Verificación:* test de integración valida el orden esperado dado un
      conjunto de predicciones de ejemplo.

- [ ] **TASK-025** [REQ-012] Implementar `GET /municipios/{id}/recursos`
      (recomendación de nivel de atención según riesgo vigente).
      *Verificación:* test de integración devuelve recomendación coherente
      con el nivel de riesgo almacenado.

- [ ] **TASK-026** [REQ-016] Implementar `GET /modelo/desempeno` (métricas
      de precisión espacial y anticipación calculadas sobre un periodo).
      *Verificación:* test con datos de ejemplo de predicciones y brotes
      confirmados calcula correctamente precisión espacial.

---

## Fase 5 — Dashboard (frontend)

*Meta de la fase: interfaz funcional diferenciada por rol, con mapas de
calor navegables.*

- [ ] **TASK-027** [REQ-006] Implementar vista de mapa de calor
      (React + Leaflet/Mapbox) consumiendo `GET /zonas/riesgo`, con
      selector de nivel de agregación (zona/municipio/departamento).
      *Verificación:* prueba manual — el mapa cambia de color según nivel de
      riesgo y responde al cambio de agregación.

- [ ] **TASK-028** [REQ-007] Implementar vista simplificada para autoridades
      (indicadores generales, zonas críticas) y vista detallada para
      epidemiólogos/equipos técnicos (variables, confianza, historial).
      *Verificación:* prueba manual con dos usuarios de rol distinto
      confirma diferencias de UI acorde a REQ-007.

- [ ] **TASK-029** [REQ-008] Implementar vista de historial de predicciones
      vs. brotes confirmados, con filtro por zona y fecha.
      *Verificación:* prueba manual sobre datos de ejemplo cargados en
      Fase 2.

- [ ] **TASK-030** [REQ-009] Implementar panel de alertas activas con
      justificación visible (variables explicativas).
      *Verificación:* prueba manual — cada alerta mostrada incluye al menos
      una variable explicativa (nunca una alerta "vacía").

- [ ] **TASK-031** [REQ-011, REQ-012] Implementar vista de priorización de
      campañas de fumigación y recomendación de recursos por municipio.
      *Verificación:* prueba manual con coordinador municipal de ejemplo.

---

## Fase 6 — Pruebas y validación

*Meta de la fase: confirmar que el sistema cumple los NFR críticos antes de
considerarse listo para el piloto.*

- [ ] **TASK-032** [NFR-010] Escribir pruebas unitarias para módulos de
      ingesta, limpieza y predicción, alcanzando cobertura mínima del 70%
      en esos módulos.
      *Verificación:* `pytest --cov=app/etl --cov=app/ml` reporta ≥ 70%.

- [ ] **TASK-033** [NFR-004] Realizar prueba de carga básica sobre
      `GET /zonas/riesgo` con un dataset simulado de hasta 350 municipios.
      *Verificación:* p95 de latencia < 2 segundos en el entorno de prueba.

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

- [ ] **TASK-036** Documentar en el informe final del proyecto universitario
      las limitaciones conocidas (sesgo de vigilancia, retraso de reporte,
      cobertura climática irregular) y cómo el sistema las mitiga
      parcialmente.
      *Verificación:* sección de limitaciones presente en el informe final.

---

## Notas de alcance

- Las tareas de Fase 5 (dashboard) pueden simplificarse a una interfaz
  mínima si el tiempo del proyecto universitario es limitado, priorizando
  siempre Fases 1-4 (backend, datos y predicción), que son el núcleo técnico
  evaluable del sistema.
- Las preguntas abiertas de `design.md` §10 (fuente de datos climáticos,
  fuente epidemiológica, zona piloto exacta) deben resolverse **antes** de
  TASK-008 y TASK-009 para evitar retrabajo.
