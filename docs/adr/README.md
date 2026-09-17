# Architecture Decision Records (ADR) — SIPTB

Registro de decisiones de arquitectura del proyecto de predicción temprana de
brotes de dengue/malaria.

**Formato:** cada ADR incluye contexto, alternativas consideradas, decisión y
justificación, además de consecuencias.
**Sección del backlog:** Architecture
**Documentos fuente:** `dengue-malaria-prediccion/design.md`, `CONTEXT.md`

## Índice

| ADR | Título | Estado |
|---|---|---|
| [ADR-001](./ADR-001-postgresql-postgis.md) | PostgreSQL 16 + PostGIS como base de datos | Aceptado |
| [ADR-002](./ADR-002-python-fastapi.md) | Python 3.12 + FastAPI para el backend | Aceptado |
| [ADR-003](./ADR-003-despliegue-railway.md) | Railway como plataforma de despliegue | Aceptado |

## ADRs candidatos (pendientes)

Estas decisiones ya están tomadas en `design.md` pero aún no tienen ADR
formal. Se documentarán si el equipo las considera relevantes:

- Modelado ML: scikit-learn / XGBoost (baseline) + SHAP para explicabilidad.
- Ejecución del pipeline de predicción: batch semanal (no tiempo real).
- Autenticación: JWT (OAuth2 password flow) con RBAC.
- Entrenamiento offline (Google Colab / servidor universitario).
