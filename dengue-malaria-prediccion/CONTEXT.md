# CONTEXT.md — Bitácora de sesión del proyecto

> ⏸️ **Desarrollo del backend en pausa.** Esta bitácora es de la carpeta
> `dengue-malaria-prediccion/` (especificación y esqueleto del backend). El
> trabajo activo de esta evaluación está en `../docs/`, `../scripts/` y
> `../data/`, documentado en `../docs/cierre_sprint1.md`, no aquí.

## Bloque de reanudación

- **Tarea activa:** ninguna tarea de `tasks.md` (Fase 1 en adelante) ha
  arrancado todavía — sigue siendo correcto no empezar TASK-001 hasta
  cerrar esta primera evaluación (ver `docs/cierre_sprint1.md`).
- **Fase actual:** Sprint 1 de la evaluación (Discovery/Data/Architecture/
  Risk/Build-QA-Deploy), no Fase 1 de `tasks.md` todavía.
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

- Zona piloto oficial: de facto son los 4 municipios con cruce real de
  clima+epidemiología (Guayaramerín, Ixiamas, Palos Blancos, San
  Buenaventura), pendiente de confirmación formal del equipo.
- Necesidad de notificaciones por correo electrónico para alertas en esta
  primera versión.
- Frecuencia de reentrenamiento del modelo.
- Si la fuente epidemiológica ofrecerá series semana-a-semana por
  municipio, o si el proyecto debe operar permanentemente con acumulados.

## Divergencias pendientes

- El pipeline de limpieza/imputación de datos (TASK-010, adelantado como
  prototipo en Sprint 1) no está subido al repositorio por el bloqueo de
  DVC descrito arriba — no es una divergencia de diseño, es un impedimento
  de acceso a credenciales.
