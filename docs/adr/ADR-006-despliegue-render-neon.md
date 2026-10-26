# ADR-006: Render + Neon como plataforma de despliegue

- **Estado:** Aceptado
- **Fecha:** 2026-10-26
- **Decisores:** Equipo SIPTB
- **Reemplaza a:** [ADR-003](./ADR-003-despliegue-railway.md)
- **Relacionado:** `design.md` §1 y §10, ADR-001, `docs/guia_despliegue_render_neon.md`

## Contexto

ADR-003 eligió Railway. Al preparar el despliegue (TASK-004) se comprobó que
Railway no es gratuito de forma sostenida (crédito de prueba único o plan de pago
mensual) y que su base PostGIS es una plantilla de contenedor sin garantías de
respaldo. El proyecto es universitario y necesita una API pública con HTTPS y una
base PostgreSQL con PostGIS (ADR-001) sin costo recurrente.

## Alternativas consideradas

1. **Render (API) + Neon (base) + GitHub Actions (cron)**: todo gratuito.
2. Railway con plan de pago.
3. Northflank (servicios, jobs y una base en un solo plan gratuito): no se
   confirmó soporte de PostGIS.
4. Servidor propio o de la universidad con `docker compose`.
5. Google Cloud Run + Cloud Scheduler: requiere tarjeta.

## Decisión

La API (imagen `api` del `Dockerfile`) se despliega en un servicio web gratuito de
Render; la base PostgreSQL 16 + PostGIS vive en Neon (región us-east-2, la misma
que la de Render); el job semanal (TASK-016) se disparará desde GitHub Actions.

## Justificación

- Cada pieza tiene plan gratuito y Neon soporta PostGIS (verificado: 3.3.10).
- La imagen es la misma en local y en la nube; no hay archivos propios de un
  proveedor (se eliminó `railway.toml`).
- Las migraciones se aplican al arrancar (`RUN_MIGRATIONS=1` en el `CMD`).

## Consecuencias

- **Positivas:** costo cero; despliegue automático en cada push a la rama
  conectada; HTTPS incluido.
- **Negativas / riesgos:**
  - La API gratuita se duerme tras 15 minutos sin tráfico y la primera petición
    tarda cerca de un minuto (NFR-003, disponibilidad del 99 %, no queda garantizado).
  - Neon gratuito: del orden de 0,5 GB y el cómputo se suspende sin uso.
  - El job semanal no puede vivir en la API dormida: necesita un cron externo.
  - Tres paneles y secretos repartidos entre Render, Neon y GitHub.
  - Sin copias de seguridad garantizadas: conviene hacer `pg_dump` periódicos.
- **Verificación (2026-10-26):** `GET /health` responde 200 por HTTPS con
  certificado válido; `http://` redirige con 301; la API consulta la base de Neon.
