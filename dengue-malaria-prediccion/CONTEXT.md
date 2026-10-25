# CONTEXT.md — Bitácora de sesión del proyecto

> ▶️ **Desarrollo del backend retomado el 2026-10-25.** La Primera
> Evaluación ya cerró con evidencia (ver `../docs/cierre_sprint1.md`), por
> lo que el bloqueo de este archivo quedó resuelto. Fase 1 y parte de la
> Fase 2 de `tasks.md` ya tienen código real — ver bloque de reanudación.

## Bloque de reanudación

- **Tarea activa:** TASK-005 a TASK-010 implementadas y verificadas en esta
  sesión (2026-10-25, Tania). **Pendiente antes de marcarlas `[x]` en
  `tasks.md`:** confirmar con el equipo las divergencias listadas abajo
  (regla de `CLAUDE.md`: no marcar `[x]` sin confirmar que no hubo
  divergencia respecto a `design.md`).
- **Fase actual:** Fase 1 (Infraestructura base) y Fase 2 (Capa de datos)
  de `tasks.md`, ya no Sprint 1 de la evaluación.
- **Estado:** el proyecto ya tiene EDA real (no sintético), reglas de
  calidad documentadas, C4, métricas de valor y cierre de sprint escritos.
  Ver `docs/cierre_sprint1.md` para el estado tarea-por-tarea de todo el
  equipo, verificado contra el repositorio.
- **Bloqueos:** el remoto DVC (`origin-s3`, DagsHub) configurado para
  versionar `data/raw/` no tiene credenciales disponibles en esta máquina;
  `dvc pull` falla. Reconfirmado con evidencia el 2026-09-17 (ver
  `docs/entorno_datos_iniciales.md` §6.1); ya no bloquea solo a Tania, sino
  a cualquier máquina nueva que clone el repo sin credenciales de DagsHub.
- **Resuelto (2026-09-17):** en Python 3.13, `psycopg2-binary==2.9.9` y
  `shap==0.46.0` no instalaban por falta de *wheels* precompilados para esa
  versión de Python. Se decidió la Opción B (`docs/entorno_datos_iniciales.md`
  §5.3): se actualizaron a `psycopg2-binary==2.9.13`, `shap==0.52.0` y
  `numpy==2.5.3` en `dengue-malaria-prediccion/requirements.txt`, verificado
  con instalación limpia y una prueba funcional real de SHAP+XGBoost antes
  de aplicar el cambio. También se fijaron las 9 versiones del
  `requirements.txt` raíz a las ya verificadas en esta sesión.

## Registro de sesiones

| Sesión | Fecha | Resumen | Archivos afectados |
|---|---|---|---|
| 4 | 2026-10-25 | Tania retomó el backend. Se resolvieron las 2 preguntas abiertas de `design.md` §10 (zona piloto: se confirman los 4 municipios de facto; granularidad epidemiológica: CORREGIDO a acumulado SE1-13 real, no semanal — `docs/resultados_linea_base.md` Exp. C/D confirma que la serie municipio-semana no existe y no puede derivarse sin fabricar datos). Se implementaron y verificaron TASK-005 a TASK-010: modelos ORM + migración Alembic (PostgreSQL 16 + PostGIS 3.4 local), conector climático (`app/etl/conectores/senamhi.py`), conector epidemiológico acumulado (`app/etl/conectores/epidemiologia.py`), y el módulo de limpieza/imputación (`app/etl/limpieza.py`, con el paso de calendario diario global que faltaba para no subestimar los huecos reales). Se corrió el pipeline completo contra los datos reales de `data/processed/` (274 filas de clima, 4 dengue, 3 malaria insertadas; luego revertidas con TRUNCATE para no ensuciar la BD de desarrollo antes de dejarla a los tests). 14/14 tests pasan, 89% cobertura en `app/etl` y `app/models`. | app/core/database.py, app/models/*, app/etl/*, alembic/*, tests/*, .env (no versionado), CONTEXT.md |
| 1 | 2026-08-24 | Se generó la documentación inicial completa (requirements.md, design.md, tasks.md) a partir de la solicitud de cambio original y la entrevista de stack/despliegue/herramientas. | requirements.md, design.md, tasks.md, CLAUDE.md, .github/copilot-instructions.md, CONTEXT.md |
| 2 | 2026-09-16 | Se resolvieron con datos reales las dos primeras preguntas abiertas de `design.md` §10 (fuente climática y epidemiológica) a partir del EDA de Adriana. Tania completó C4, métricas de valor y cierre de Sprint 1; construyó (sin subir todavía) el pipeline de limpieza/imputación. Se detectó y corrigió la inconsistencia de precisión entre `product_goal.md` y NFR-001/NFR-002, y se documentó el bloqueo de credenciales de DVC. | design.md, product_goal.md, tasks.md, docs/c4/, docs/metricas_valor.md, docs/cierre_sprint1.md, CONTEXT.md |
| 3 | 2026-09-17 | Ignacio cerró sus dos tareas pendientes del backlog de Sprint 1. (a) Privacidad y licencias: se confirmó con evidencia de columnas que ninguna fuente usada expone datos de pacientes, y se leyó el marco legal boliviano real (DAT-002, CTIC-EPB 2019) para las licencias de Ministerio de Salud/SENAMHI/SEDES. (b) Línea Base — Paso 1: se crearon y probaron de punta a punta dos entornos venv (raíz y backend) en una máquina limpia, se confirmó el bloqueo real de `dvc pull` y se documentó el estado inicial de los datos crudos (no disponibles) vs. procesados (preexistentes). Se encontraron y documentaron (sin corregir unilateralmente) dos paquetes del backend incompatibles con Python 3.13. | docs/privacidad_datos.md, docs/fuentes_legales/, docs/entorno_datos_iniciales.md, docs/evidencia_entorno/, docs/cierre_sprint1.md, README.md (backend), CONTEXT.md |

## Decisiones clave

- **Stack:** Python + FastAPI + PostgreSQL (decisión del usuario).
- **Extensión PostGIS:** agregada por necesidad de análisis geoespacial
  (mapas de calor por zona/municipio/departamento), no era explícita en el
  pedido original pero se infiere de los requisitos.
- **Despliegue:** Railway, sugerido por Claude y aceptado por el usuario,
  con alternativa de entrenar el modelo offline (Colab/servidor universidad)
  si el cómputo de Railway resulta insuficiente para el entrenamiento.
- **Ejecución del pipeline de predicción:** batch semanal (no tiempo real),
  decisión de diseño razonable dado el horizonte de predicción de 3-4
  semanas; queda como supuesto a confirmar con el usuario.
- **Fuente climática confirmada:** SENAMHI Bolivia (WIS 2.0).
- **Fuente epidemiológica confirmada:** Ministerio de Salud y Deportes de
  Bolivia, Boletín Epidemiológico N.º 13, 2026 (acumulados municipales
  SE1-13, no series semanales — ver limitación abajo).

## Preguntas abiertas (ver detalle en `design.md` §10)

- ~~Zona piloto oficial~~ **Resuelto (2026-10-25):** se confirman los 4
  municipios de facto (Guayaramerín, Ixiamas, Palos Blancos, San
  Buenaventura) como zona piloto oficial — únicos con cruce real de datos.
- ~~Granularidad epidemiológica~~ **Resuelto (2026-10-25):** el proyecto
  opera con el acumulado SE1-13 por municipio (lo único que la fuente
  entrega); no se construye una serie semanal porque no existe el dato base
  para hacerlo sin fabricarlo (ver `docs/resultados_linea_base.md` Exp. D).
  Mejora futura: solicitar a SEDES/Min. de Salud el desagregado semanal.
- Necesidad de notificaciones por correo electrónico para alertas en esta
  primera versión.
- Frecuencia de reentrenamiento del modelo.

## Divergencias pendientes (confirmar antes de marcar TASK-005/010 como `[x]`)

- ~~El pipeline de limpieza/imputación de datos (TASK-010, adelantado como
  prototipo en Sprint 1) no está subido al repositorio~~ **Resuelto:**
  `scripts/limpieza_datos.py` sí está en el repo (no depende de DVC, solo
  los datos crudos que consume). Se reutilizó su lógica en
  `app/etl/limpieza.py` tal como pedía la nota de la tarea.
- **Granularidad epidemiológica (TASK-009):** `fecha_reporte` no representa
  un reporte diario ni semanal real — es el domingo de la SE13 del año,
  fecha de cierre del periodo acumulado SE1-13 (única granularidad que la
  fuente entrega). Documentado en el docstring del conector. Si en el
  futuro el Min. de Salud entrega series semanales, este conector deberá
  rehacerse (no extenderse).
- **`casos_epidemiologicos`:** se agregó una `UNIQUE(municipio_id,
  enfermedad_id, fecha_reporte, fuente)` no especificada en `design.md` §3,
  para poder reingerir sin duplicar. No contradice el diseño, lo completa.
- **`municipios.geometria`:** es un cuadrado referencial (~5 km) centrado en
  la coordenada real de la estación SENAMHI de cada municipio piloto, NO el
  polígono administrativo oficial del INE (no se tenía ese archivo
  disponible). Pendiente: cargar el polígono real antes de calcular áreas o
  cualquier métrica espacial que dependa de la forma exacta del municipio.
- **`app/core/database.py`:** se creó con lo mínimo (Base, engine, sesión)
  para que los modelos y Alembic funcionaran, adelantándose parcialmente a
  TASK-003 (config.py, de Ignacio). Revisar que no se dupliquen al
  implementar TASK-003.
