# CONTEXT.md — Bitácora de sesión del proyecto

## Bloque de reanudación

- **Tarea activa:** TASK-001 (inicialización de estructura de proyecto)
- **Fase actual:** Fase 1 — Infraestructura base
- **Estado:** No iniciado (documentación de especificación recién completada)
- **Bloqueos:** Ninguno registrado. Pendiente resolver las preguntas
  abiertas de `design.md` §10 (fuente de datos climáticos, fuente
  epidemiológica y zona piloto exacta) antes de llegar a TASK-008/TASK-009.

## Registro de sesiones

| Sesión | Fecha | Resumen | Archivos afectados |
|---|---|---|---|
| 1 | 2026-08-24 | Se generó la documentación inicial completa (requirements.md, design.md, tasks.md) a partir de la solicitud de cambio original y la entrevista de stack/despliegue/herramientas. | requirements.md, design.md, tasks.md, CLAUDE.md, .github/copilot-instructions.md, CONTEXT.md |

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

## Preguntas abiertas (pendientes de mover a design.md cuando se resuelvan)

- Fuente exacta de datos climáticos públicos.
- Fuente exacta de datos epidemiológicos históricos.
- Zona piloto específica para validar precisión espacial (75%) y
  anticipación (2 semanas).
- Necesidad de notificaciones por correo electrónico para alertas en esta
  primera versión.
- Frecuencia de reentrenamiento del modelo.

## Divergencias pendientes

Ninguna todavía — el proyecto está en fase de documentación, sin código
implementado.
