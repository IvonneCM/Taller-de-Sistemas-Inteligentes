# Cierre de Sprint 1 — backlog pendiente, bloqueos y próximos pasos

**Responsable:** Tania Perez
**Sección del backlog:** Discovery
**Uso previsto:** insumo del punto 7 de la presentación ("Gestión y Cierre")

---

## 1. Estado real de las 17 tareas de Sprint 1

Este estado se verificó directamente contra el repositorio (`git log`,
archivos en `docs/`), no contra lo que dice ClickUp, para evitar reportar
como "Done" algo que en el repo no existe todavía.

### Completadas y ya mergeadas a `tani`

| Tarea | Responsable | Evidencia |
|---|---|---|
| EDA inicial, climático e integrado con datos reales | Adriana | `docs/eda_inicial.md`, `scripts/eda_*.py` |
| Reglas de calidad, limpieza e imputación de datos | Dilan | `docs/reglas_calidad_datos.md` |
| Controles de seguridad desde el diseño | Dilan | `docs/controles_seguridad.md` |
| README actualizado con estado y guía de reproducción | Dilan | `dengue-malaria-prediccion/README.md` |
| Configuración de DVC y versionado de datos raw | Adriana | commit `b2b79a4` (ver bloqueo §3.1) |
| Diagramas C4 (Contexto y Contenedores) | Tania | `docs/c4/` |
| Métricas de valor y criterios de éxito | Tania | `docs/metricas_valor.md` |

### Pendientes — sin ningún artefacto todavía en el repositorio

Se revisó `docs/`, `docs/adr/`, y las ramas remotas de cada integrante; estos
archivos no existen en ninguna rama al momento de este cierre:

| Tarea | Responsable | Lista |
|---|---|---|
| Alcance y exclusiones (resumen para la presentación) | Ivonne | Discovery |
| Inventario de fuentes de datos epidemiológicos y climáticos | Ivonne | Data |
| Registro de decisiones de arquitectura (ADR) | Ivonne | Architecture |
| Línea base — Paso 3 (registro de experimentos) | Ivonne | Build/QA/Deploy |
| Declaración de uso de IA y revisión humana | Adriana | Discovery |
| Risk Register inicial | Adriana | Risk |
| Evidencia de Sprint 1 (backlog organizado, Product Goal enlazado) | Ignacio | Discovery |
| Restricciones de privacidad y licencias de datos | Ignacio | Data |
| Línea base — Paso 1 (entorno y datos iniciales) | Ignacio | Build/QA/Deploy |

### Bloqueada por un impedimento técnico (no por falta de trabajo)

| Tarea | Responsable | Estado real |
|---|---|---|
| Pipeline reproducible de datos (Línea base — Paso 2) | Tania | Construido y probado localmente (`scripts/limpieza_datos.py`, resultados verificados), **pendiente de subir al repositorio** hasta resolver el bloqueo de DVC (§3.1). No se fuerza el commit para no dejar en el repo una "evidencia reproducible" que en realidad nadie más puede reproducir. |

## 2. Backlog pendiente para el siguiente sprint

1. Terminar y subir el pipeline de limpieza (Tania) en cuanto se resuelva
   el acceso a DVC — ya no requiere trabajo de diseño, solo desbloqueo de
   credenciales y commit.
2. Completar las 9 tareas listadas como "pendientes" arriba (Ivonne,
   Adriana, Ignacio) — ninguna tiene contenido en el repo todavía.
3. ~~Reconciliar la cifra de precisión del modelo entre `product_goal.md`
   y `requirements.md` NFR-001~~ — **Resuelto:** `product_goal.md` ahora cita
   directamente NFR-001 (75%) y NFR-002 (mínimo 2 semanas, objetivo 3-4)
   en vez de repetir números sueltos.
4. Decidir formalmente si los 4 municipios con datos reales cruzados
   (Guayaramerín, Ixiamas, Palos Blancos, San Buenaventura) son la zona
   piloto oficial, o si se sigue buscando otra — `design.md` §10 sigue
   listándolo como pregunta abierta pese a que el EDA ya opera de facto
   con esos 4.
5. Resolver la limitación temporal documentada en `docs/eda_inicial.md`
   §16: pasar de acumulados SE1-13 municipales a series municipio-semana,
   condición necesaria para poder medir NFR-001/NFR-002 con datos reales.
6. Una vez cerrada esta evaluación, retomar `tasks.md` desde TASK-001 con
   `FIRST_PROMPT.md` para el desarrollo real del backend (no antes: esta
   evaluación es sobre decisiones y evidencia, no sobre sistema funcionando
   de punta a punta).

## 3. Bloqueos actuales y plan de resolución

### 3.1 Acceso a DVC (bloqueo activo, detectado hoy)

**Qué pasó:** el commit `b2b79a4` (Adriana) configuró DVC contra un remoto
S3 en DagsHub (`dagshub.com/AdrianaRochaVedia/...`) y movió los CSV raw de
clima y epidemiología de git plano a punteros `.dvc`. Al traer ese commit,
los archivos raw reales **desaparecieron del working tree** de quien no
tenga ya una copia local, y `dvc pull -r origin-s3` falla con
`Unable to locate credentials` — se verificó directamente en esta máquina.

**Impacto:** cualquiera que clone el repo desde cero hoy (incluido el
docente) no puede reproducir `descargar_senamhi.py → procesar_clima.py →
integrar_datos.py` ni el nuevo pipeline de limpieza, porque el insumo raw
no es accesible sin credenciales de ese remoto.

**Plan de resolución:**
1. Pedir a Adriana las credenciales del remoto `origin-s3` (o agregar al
   equipo como colaboradores del repositorio DagsHub) y confirmar si ella
   ya ejecutó `dvc push` — si no lo hizo, los datos ni siquiera están en el
   remoto todavía.
2. Una vez resuelto, decidir como equipo qué CSV de `data/processed/`
   entran a DVC (hoy la mayoría sigue en git plano, incluidos los
   originales de Adriana) para no dejar el repositorio con dos
   convenciones mezcladas.
3. Recién entonces subir el pipeline de limpieza de Tania.

**No es un bloqueo de diseño ni de código** — el trabajo del pipeline en sí
está terminado; el bloqueo es exclusivamente de acceso/credenciales.

### 3.2 Fuentes epidemiológicas semanales por municipio

Los datos oficiales disponibles son acumulados SE1-13 a nivel municipal, no
series semanales. Esto limita qué se puede medir hoy (ver
`docs/metricas_valor.md` §4). Plan: gestionar con el Ministerio de Salud o
SEDES si existe un desglose semanal municipal, o documentar explícitamente
que el MVP de esta evaluación trabaja con acumulados y que la serie
semanal es un requisito para el sprint de desarrollo real.

### 3.3 Catálogo oficial de municipios de Bolivia

La validación epidemiológica del pipeline (COM-01) es hoy estructural
(no vacío, no duplicado) porque no existe todavía una tabla de referencia
oficial de municipios en el proyecto. Plan: Ignacio/Ivonne la agregan como
parte del inventario de datos.

## 4. Viabilidad del proyecto (evaluación breve)

- **Viable a nivel de datos:** ya existen datos reales (no sintéticos) de
  SENAMHI y del Ministerio de Salud, con un pipeline de ingesta,
  control de calidad y (pendiente de subir) imputación que funciona sobre
  esos datos reales. Esto es más avanzado que lo esperado para una primera
  evaluación de "decisiones iniciales justificadas".
- **Riesgo principal no técnico:** la coordinación de acceso compartido
  (DVC) y la cantidad de tareas del equipo aún sin ningún artefacto en el
  repo (9 de 17) son el mayor riesgo para llegar a la defensa con el
  checklist completo, más que cualquier limitación de los datos en sí.
- **Riesgo técnico principal:** la granularidad temporal de los datos
  epidemiológicos (acumulados, no semanales) impide validar hoy las dos
  métricas de éxito centrales del producto (NFR-001, NFR-002). Es un
  riesgo conocido y documentado, no oculto.
- **Conclusión:** el proyecto es viable para presentar en esta evaluación
  con evidencia real y honesta (datos, pipeline, limitaciones explícitas),
  pero requiere que el resto del equipo cierre su backlog pendiente antes
  de la fecha de defensa.
