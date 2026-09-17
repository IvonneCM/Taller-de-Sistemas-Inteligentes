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

### Completada tras resolver el bloqueo técnico

| Tarea | Responsable | Evidencia |
|---|---|---|
| Pipeline reproducible de datos (Línea base — Paso 2) | Tania | `scripts/limpieza_datos.py`, `docs/pipeline_datos.md`. Quedó bloqueada por falta de credenciales de DVC (§3.1); se desbloqueó cuando Adriana agregó a Tania como colaboradora en DagsHub. |

## 2. Backlog pendiente para el siguiente sprint

1. Completar las 9 tareas listadas como "pendientes" arriba (Ivonne,
   Adriana, Ignacio) — ninguna tiene contenido en el repo todavía.
2. Decidir formalmente si los 4 municipios con datos reales cruzados
   (Guayaramerín, Ixiamas, Palos Blancos, San Buenaventura) son la zona
   piloto oficial, o si se sigue buscando otra — `design.md` §10 sigue
   listándolo como pregunta abierta pese a que el EDA ya opera de facto
   con esos 4.
3. Resolver la limitación temporal documentada en `docs/eda_inicial.md`
   §16: pasar de acumulados SE1-13 municipales a series municipio-semana,
   condición necesaria para poder medir NFR-001/NFR-002 con datos reales.
4. Decidir como equipo si los CSV de `data/processed/` deben moverse a DVC
   para seguir la misma convención que `data/raw/`, o si se mantiene la
   convención actual (raw en DVC, processed en git plano) — ver nota en
   `docs/pipeline_datos.md`.
5. Una vez cerrada esta evaluación, retomar `tasks.md` desde TASK-001 con
   `FIRST_PROMPT.md` para el desarrollo real del backend (no antes: esta
   evaluación es sobre decisiones y evidencia, no sobre sistema funcionando
   de punta a punta).

## 3. Bloqueos actuales y plan de resolución

### 3.1 Acceso a DVC — RESUELTO

**Qué pasó:** el commit `b2b79a4` (Adriana) configuró DVC contra un remoto
S3 en DagsHub (`dagshub.com/AdrianaRochaVedia/...`) y movió los CSV raw de
clima y epidemiología de git plano a punteros `.dvc`. Al traer ese commit,
los archivos raw reales desaparecieron del working tree de quien no tuviera
ya una copia local, y `dvc pull -r origin-s3` fallaba con
`Unable to locate credentials`.

**Impacto que tuvo:** entre el commit `b2b79a4` y la resolución de este
bloqueo, cualquiera que clonara el repo desde cero (incluido el docente) no
podía reproducir `descargar_senamhi.py → procesar_clima.py →
integrar_datos.py` ni el pipeline de limpieza, porque el insumo raw no era
accesible sin credenciales de ese remoto.

**Cómo se resolvió:** Adriana agregó a Tania como colaboradora del
repositorio en DagsHub; con ese acceso se generaron credenciales S3
("Use as S3" en la UI de DagsHub) y se configuraron localmente con
`dvc remote modify --local origin-s3 access_key_id/secret_access_key`.
Se verificó con `dvc pull -r origin-s3` que los 3 archivos raw (16.778
registros climáticos, 28 de dengue, 21 de malaria) se recuperan íntegros, y
se volvió a correr `scripts/limpieza_datos.py` de punta a punta sobre esos
datos recuperados para confirmar que el pipeline sigue siendo reproducible.

**Pendiente de decisión de equipo (no bloqueante):** `data/processed/`
sigue en git plano (igual que los archivos originales de Adriana), no en
DVC — ver ítem 4 del backlog en §2.

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
  SENAMHI y del Ministerio de Salud, con un pipeline de ingesta, control de
  calidad e imputación que funciona de punta a punta sobre esos datos
  reales y ya está subido al repositorio. Esto es más avanzado que lo
  esperado para una primera evaluación de "decisiones iniciales
  justificadas".
- **Riesgo principal no técnico:** la cantidad de tareas del equipo aún sin
  ningún artefacto en el repo (9 de 17, ver §1) es el mayor riesgo para
  llegar a la defensa con el checklist completo, más que cualquier
  limitación técnica de los datos. El riesgo de coordinación de acceso a
  DVC ya se resolvió (§3.1).
- **Riesgo técnico principal:** la granularidad temporal de los datos
  epidemiológicos (acumulados, no semanales) impide validar hoy las dos
  métricas de éxito centrales del producto (NFR-001, NFR-002). Es un
  riesgo conocido y documentado, no oculto.
- **Conclusión:** el proyecto es viable para presentar en esta evaluación
  con evidencia real y honesta (datos, pipeline, limitaciones explícitas),
  pero requiere que el resto del equipo cierre su backlog pendiente antes
  de la fecha de defensa.
