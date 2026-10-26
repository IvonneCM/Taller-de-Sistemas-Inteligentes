# Arquitectura actual del MVP (TASK-042)

Describe **lo que existe y corre hoy**, no lo aspiracional. Cada caja indica su código en el repositorio. Los diagramas C4 del Sprint 1 ([`c4/`](./c4/)) muestran el diseño objetivo; este documento es el que debe coincidir con la demostración.

Estado al 2026-10-26: todo corre en local; **no hay despliegue en la nube todavía** (TASK-004 pendiente).

```mermaid
flowchart LR
  persona["Persona usuaria<br/>(autoridad, SEDES, epidemiólogo,<br/>coordinación, admin)"]

  subgraph web["Contenedor web"]
    spa["Interfaz React + Leaflet<br/>frontend/src"]
  end

  subgraph api["Contenedor api (FastAPI)"]
    rutas["Rutas y control de acceso por rol<br/>app/api"]
    servicios["Servicios de consulta<br/>app/services"]
    obs["Logs y errores uniformes<br/>app/core/observabilidad.py"]
  end

  subgraph db["PostgreSQL 16 + PostGIS"]
    tablas[("municipios · casos_epidemiologicos<br/>datos_climaticos · modelos · predicciones<br/>alertas · umbrales · brotes_confirmados<br/>usuarios · roles · refresh_tokens")]
  end

  subgraph ml["Job de datos y predicción (imagen ml)"]
    etl["Ingesta y limpieza<br/>app/etl"]
    modelo["Features + XGBoost + SHAP<br/>app/ml"]
  end

  csv[("CSV procesados<br/>data/processed (DVC)")]
  fuentes["Boletín Epidemiológico N.º 13<br/>SENAMHI / NASA POWER"]

  persona -->|HTTPS| spa
  spa -->|"/api (JWT)"| rutas
  rutas --> servicios --> tablas
  rutas -.-> obs
  fuentes -->|"scripts/pipeline_completo.py"| csv
  csv --> etl --> tablas
  csv --> modelo
  modelo -->|"INSERT predicciones<br/>(inmutables)"| tablas
```

Lectura del flujo observable en la demostración: **persona → interfaz → API → servicios → base de datos ← modelo**. La API nunca ejecuta el modelo: lee las predicciones que el job guardó.

## Contenedores y dónde está su código

| Pieza | Qué hace | Código | Se ejecuta con |
|---|---|---|---|
| Interfaz | Login, mapa, detalle por rol, alertas, historial | `dengue-malaria-prediccion/frontend/` | `npm run dev` · imagen `web` (nginx) |
| API | Autenticación, RBAC y consultas | `dengue-malaria-prediccion/app/` | `uvicorn app.main:app` · imagen `api` |
| Base de datos | Datos, predicciones y usuarios | `alembic/` (migraciones) | PostGIS local o `docker compose up db` |
| Ingesta y limpieza | CSV procesados → tablas | `app/etl/`, `scripts/` | `python -m app.etl.seed_demo` |
| Modelo | Features, predicción y explicación | `app/ml/` | `python -m app.ml.prediccion --modelo-id N` · imagen `ml` |
| Datos versionados | Pipeline reproducible | `dvc.yaml`, `scripts/pipeline_completo.py` | `python scripts/pipeline_completo.py` |

## Qué es código, qué es configuración y qué es secreto

| Tipo | Ejemplos | Dónde vive | ¿Se versiona? |
|---|---|---|---|
| Código | `app/`, `frontend/src/`, `alembic/` | Repositorio | Sí |
| Configuración (no secreta) | `LOG_LEVEL`, `DB_*_TIMEOUT`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ENVIRONMENT` | Variables de entorno; plantilla en `.env.example` | Solo la plantilla |
| **Secretos** | `DATABASE_URL`, `SECRET_KEY`, `SEED_DEMO_PASSWORD` | Variables de entorno o `.env` local | **Nunca** (`.env` está ignorado) |

`SECRET_KEY` y `DATABASE_URL` no tienen valor por defecto: si faltan, la aplicación no arranca (`app/core/config.py`). Con `ENVIRONMENT=production` se rechaza una clave débil.

## Decisiones que explican la forma del sistema

- **Una sola base y una API de lectura:** el modelo escribe predicciones y la API solo las consulta, así que la interfaz no depende de que el modelo esté corriendo ([ADR-001](./adr/ADR-001-postgresql-postgis.md), [ADR-002](./adr/ADR-002-python-fastapi.md)).
- **Predicciones inmutables:** solo `INSERT`, para auditoría (NFR-009).
- **Control de acceso en el servidor:** la vista resumida no recibe los campos técnicos; no se ocultan en la interfaz (REQ-007).
- **Malaria sin modelo:** solo hay acumulados, así que se muestran casos observados ([ADR-005](./adr/ADR-005-malaria-acumulado-en-bd.md)).

## Diferencias con el diseño original (`design.md`)

| Diseño original | Realidad hoy |
|---|---|
| Dashboard con selector de agregación zona, municipio y departamento | Solo municipio |
| Ingesta por `POST /datos/clima` y `/datos/casos` | La ingesta es por comando (`app/etl`), no por la API |
| `GET /campanas/priorizacion` y `/municipios/{id}/recursos` | No implementados (TASK-024 y 025) |
| Tarea programada semanal en Railway | No implementada (TASK-016); la predicción se ejecuta a mano |
| Despliegue en Railway | Pendiente (TASK-004) |
