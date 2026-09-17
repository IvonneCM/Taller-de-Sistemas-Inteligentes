# ADR-003: Railway como plataforma de despliegue

- **Estado:** Aceptado
- **Fecha:** 2026-09-16
- **Decisores:** Equipo SIPTB (sugerido y aceptado por el usuario)
- **Relacionado:** `design.md` §1, `CONTEXT.md` (decisiones clave), ADR-001

## Contexto

El sistema (API FastAPI + PostgreSQL/PostGIS) debe desplegarse para el piloto y
la demostración, con bajo esfuerzo operativo, dado que es un proyecto
universitario con equipo pequeño y presupuesto limitado. El entrenamiento del
modelo es intensivo en cómputo y no necesita ejecutarse en el entorno de
producción.

## Alternativas consideradas

1. **Railway** — PaaS con Postgres administrado y despliegue simple.
2. **Heroku** — PaaS maduro, pero con costos/planes menos flexibles hoy.
3. **Render** — alternativa PaaS similar, con soporte de Postgres.
4. **Fly.io** — más control de infraestructura, mayor curva de aprendizaje
   (contenedores y volúmenes).
5. **VPS / nube (AWS, GCP, Azure)** — mayor control, pero implica administrar
   red, backups y seguridad, desproporcionado para el alcance.

## Decisión

Desplegar en **Railway** la API y la base de datos PostgreSQL/PostGIS, y
**entrenar el modelo offline** (Google Colab o servidor de la universidad).
La decisión fue sugerida por el asistente y **aceptada por el usuario** (ver
`CONTEXT.md`).

## Justificación

- Ofrece **PostgreSQL administrado**, compatible con el requisito de PostGIS
  (ADR-001) y con Alembic.
- Reduce el esfuerzo operativo (deploy desde repositorio, variables de entorno,
  logs) — adecuado para un equipo sin SRE dedicado.
- El cómputo de entrenamiento queda fuera de producción, evitando sobrecargar
  un entorno liviano.

## Consecuencias

- **Positivas:** despliegue rápido, menor carga operativa, costo contenido para
  el piloto.
- **Negativas / riesgos:** límites de cómputo de Railway para tareas pesadas
  (mitigado con entrenamiento offline); posible dependencia del proveedor
  (vendor lock-in) y costo recurrente si el proyecto escala.
- **Pendiente de verificar:** que la instancia de Railway permita habilitar la
  extensión PostGIS; si no fuera posible, reevaluar proveedor (impacta ADR-001).
