# CLAUDE.md — Instrucciones para Claude Code

> Este archivo sigue el flujo de **Spec Driven Development (SDD)**. Antes de
> escribir o modificar código, lee siempre `requirements.md`, `design.md`,
> `tasks.md` y `CONTEXT.md` (en ese orden, empezando por CONTEXT.md si
> existe una sesión previa).

## Bloque de instrucciones universal (compartido con otros agentes de IA)

### Proyecto

Sistema inteligente de predicción temprana de brotes de dengue/malaria en
Bolivia, orientado a autoridades de salud pública, equipos del SEDES,
médicos epidemiólogos y coordinadores sanitarios municipales. Objetivo:
anticipar brotes con 3-4 semanas de anticipación usando datos
epidemiológicos, climáticos y geoespaciales.

### Stack

- Backend: Python 3.12 + FastAPI
- Base de datos: PostgreSQL 16 + PostGIS
- ML: scikit-learn / XGBoost + SHAP (explicabilidad)
- Frontend: React + Leaflet/Mapbox
- Despliegue: Railway

### Reglas no negociables

1. **No inventar datos reales no verificados.** Cualquier cifra epidemiológica,
   climática o de desempeño del modelo que no provenga de una fuente
   verificada dentro del proyecto debe marcarse explícitamente como
   "estimada" o "referencial" en código, comentarios y documentación.
2. **No incluir datos personales de pacientes** en ningún modelo, endpoint,
   log o archivo de prueba. Todo dato epidemiológico es agregado por
   municipio y fecha (ver REQ-020).
3. **No generar alertas sin justificación.** Cualquier lógica que cree un
   registro en `alertas` debe garantizar que exista al menos una variable
   explicativa asociada (ver REQ-005, TASK-015).
4. **Toda predicción es inmutable tras su creación** (solo INSERT, nunca
   UPDATE sobre la tabla `predicciones`), para permitir auditoría (NFR-009).
5. **Seguir `requirements.md` como fuente de autoridad.** Si una tarea de
   código implica una decisión no cubierta por `requirements.md` o
   `design.md`, detente y pregunta antes de asumir — no fabricar requisitos.
6. **No exponer credenciales** (claves de BD, API keys climáticas) en código,
   commits, ni en artefactos generados. Usar siempre variables de entorno.
7. **Referenciar REQ-xxx/NFR-xxx** en el mensaje de commit o en el docstring
   de la función principal cuando el código implemente una tarea de
   `tasks.md`.

### Flujo de trabajo esperado

1. Leer `CONTEXT.md` (si existe) para saber en qué tarea se quedó la sesión
   anterior.
2. Confirmar la tarea activa de `tasks.md` antes de escribir código.
3. Implementar solo lo necesario para esa tarea (atomicidad, ver
   `tasks.md`).
4. Ejecutar la verificación descrita en la tarea (test, comando, medición).
5. Marcar la tarea como completada solo después de confirmar que no hubo
   divergencia respecto a `design.md` (si hubo divergencia, actualizar
   `design.md` primero).
6. Actualizar `CONTEXT.md` al cierre de la sesión.

### Manejo de datos incompletos (contexto específico del dominio)

Este proyecto asume que los datos **nunca serán perfectos**:

- Puede haber retraso de reporte epidemiológico.
- Puede haber sesgo de vigilancia entre zonas.
- Los datos climáticos pueden tener cobertura irregular.

Cualquier código de ingesta o de modelado debe manejar explícitamente estos
casos (ver `app/etl/limpieza.py` y NFR-007), nunca asumir datos completos por
defecto.

---

## Instrucciones específicas de Claude Code

- Al iniciar una sesión, lee `CONTEXT.md` primero. Si no existe, pregunta
  "¿qué estamos trabajando hoy?" en vez de asumir la primera tarea de
  `tasks.md`.
- Al terminar una sesión con trabajo realizado, actualiza `CONTEXT.md` según
  el protocolo de la skill de Spec Driven Development (resumen de sesión,
  bloque de reanudación, decisiones clave, divergencias pendientes).
- Antes de marcar una tarea de `tasks.md` como `[x]`, pregunta explícitamente
  si la implementación coincidió con `design.md` o si hubo divergencia.
- Usa `pytest` para todas las verificaciones de tipo test. No uses
  frameworks de testing distintos sin justificarlo.
- Para migraciones de base de datos, usa siempre Alembic — nunca alterar el
  esquema manualmente sin generar una migración correspondiente.
