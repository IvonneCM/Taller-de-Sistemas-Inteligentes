# Cierre de Sprint 1 — backlog pendiente, bloqueos y próximos pasos

**Responsable:** Tania Perez
**Sección del backlog:** Discovery
**Uso previsto:** insumo del punto 7 de la presentación ("Gestión y Cierre")

---

## 1. Estado real de las 17 tareas de Sprint 1

Este estado se verificó directamente contra el repositorio (`git log`,
archivos en `docs/`), no contra lo que dice ClickUp, para evitar reportar
como "Done" algo que en el repo no existe todavía. **Actualización
2026-09-17: las 17 tareas de Sprint 1 tienen evidencia en el repositorio.**

| Tarea | Responsable | Lista | Evidencia |
|---|---|---|---|
| Alcance y exclusiones del proyecto | Ivonne | Discovery | `requirements.md` §6 |
| Documentar métricas de valor y criterios de éxito | Tania | Discovery | `docs/metricas_valor.md` |
| Redactar declaración de uso de IA y revisión humana | Adriana | Discovery | `docs/declaracion_uso_ia.md` |
| Actualizar README con estado y guía de reproducción | Dilan | Discovery | `dengue-malaria-prediccion/README.md` |
| Preparar evidencia de Sprint 1 (backlog, Product Goal) | Ignacio | Discovery | `docs/product_goal.md`, backlog en ClickUp |
| Inventario de fuentes de datos epidemiológicos y climáticos | Ivonne | Data | `docs/inventario_datos.md` |
| EDA inicial, climático e integrado con datos reales | Adriana | Data | `docs/eda_inicial.md`, `scripts/eda_*.py` |
| Definir reglas de calidad, limpieza e imputación de datos | Dilan | Data | `docs/reglas_calidad_datos.md` |
| Documentar restricciones de privacidad y licencias de datos | Ignacio | Data | `docs/privacidad_datos.md`, `docs/fuentes_legales/` |
| Elaborar diagramas C4 (Contexto y Contenedores) | Tania | Architecture | `docs/c4/` |
| Crear registro de decisiones de arquitectura (ADR) | Ivonne | Architecture | `docs/adr/` (4 ADR) |
| Elaborar Risk Register inicial | Adriana | Risk | `docs/risk_register.md` |
| Definir controles de seguridad desde el diseño | Dilan | Risk | `docs/controles_seguridad.md` |
| Preparar entorno y datos iniciales (Línea Base — Paso 1) | Ignacio | Build/QA/Deploy | `docs/entorno_datos_iniciales.md`, `docs/evidencia_entorno/` |
| Construir pipeline reproducible de datos (Línea Base — Paso 2) | Tania | Build/QA/Deploy | `scripts/limpieza_datos.py`, `docs/pipeline_datos.md` — quedó bloqueada por falta de credenciales de DVC (§3.1), resuelto cuando Adriana agregó a Tania como colaboradora en DagsHub |
| Establecer línea base y registrar experimentos (Línea Base — Paso 3) | Ivonne | Build/QA/Deploy | `docs/linea_base.md`, `scripts/linea_base_modelo.py` |
| Preparar cierre: backlog, bloqueos y próximos pasos | Tania | Discovery | este documento |

## 2. Backlog pendiente para el siguiente sprint

Con las 17 tareas de Sprint 1 cerradas, lo que queda pendiente es
consolidar decisiones de equipo y preparar el desarrollo real (Fase 1 de
`tasks.md`), no completar entregables de esta evaluación:

1. Decidir formalmente si los 4 municipios con datos reales cruzados
   (Guayaramerín, Ixiamas, Palos Blancos, San Buenaventura) son la zona
   piloto oficial, o si se sigue buscando otra — `design.md` §10 sigue
   listándolo como pregunta abierta pese a que el EDA ya opera de facto
   con esos 4.
2. Resolver la limitación temporal documentada en `docs/eda_inicial.md`
   §16: pasar de acumulados SE1-13 municipales a series municipio-semana,
   condición necesaria para poder medir NFR-001/NFR-002 con datos reales.
3. ~~Decidir como equipo si los CSV de `data/processed/` deben moverse a
   DVC~~ — **Resuelto:** Ivonne/Ignacio agregaron `dvc.yaml`/`dvc.lock`
   (commit `ef23170`), que registra `scripts/limpieza_datos.py` y los demás
   scripts como stages formales del pipeline DVC con salidas `cache: false`
   — los CSV siguen en git plano (legibles, diffeables), pero DVC verifica
   su reproducibilidad contra el hash de sus dependencias. Esta sesión
   detectó que ese `dvc.lock` había quedado desactualizado (`dvc status`
   marcaba todos los stages como modificados, probablemente por diferencias
   de fin de línea entre máquinas al hacer checkout); se corrigió
   ejecutando `dvc repro`, que confirmó que los resultados son idénticos
   (solo cambia el timestamp de generación y ruido de punto flotante en el
   último dígito de algunas correlaciones).
4. Conseguir un catálogo oficial de municipios de Bolivia para reforzar la
   validación epidemiológica (COM-01) — limitación documentada en
   `docs/inventario_datos.md` y en `docs/pipeline_datos.md`.
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
oficial de municipios en el proyecto. `docs/inventario_datos.md` (Ivonne)
confirma y documenta formalmente esta misma limitación ("sin tabla de
referencia de municipios del INE"); sigue sin resolverse, pero ya no es un
hallazgo aislado de este documento sino una limitación reconocida por el
equipo.

## 4. Viabilidad del proyecto (evaluación breve)

- **Viable a nivel de datos:** ya existen datos reales (no sintéticos) de
  SENAMHI y del Ministerio de Salud, con un pipeline de ingesta, control de
  calidad e imputación que funciona de punta a punta sobre esos datos
  reales y ya está subido al repositorio. Esto es más avanzado que lo
  esperado para una primera evaluación de "decisiones iniciales
  justificadas".
- **Riesgo principal no técnico:** ya no es la falta de artefactos — las 17
  tareas de Sprint 1 tienen evidencia en el repositorio (§1). El riesgo que
  queda es de calidad de la exposición: que cada integrante pueda explicar
  sin leer el criterio de aceptación de sus propias tareas, como exige el
  checklist de la guía de defensa.
- **Riesgo técnico principal:** la granularidad temporal de los datos
  epidemiológicos (acumulados, no semanales) impide validar hoy las dos
  métricas de éxito centrales del producto (NFR-001, NFR-002). Es un
  riesgo conocido y documentado, no oculto.
- **Conclusión:** el proyecto es viable para presentar en esta evaluación
  con evidencia real y honesta (datos, pipeline, arquitectura, riesgos,
  privacidad, línea base y limitaciones explícitas). El trabajo restante es
  de ensayo y coherencia de discurso, no de contenido faltante.
