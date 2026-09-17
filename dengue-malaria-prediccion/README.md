# Sistema de Predicción Temprana de Brotes de Dengue/Malaria

Proyecto universitario orientado a apoyar a SEDES, autoridades de salud y
coordinadores municipales en la identificación de zonas con riesgo de brotes
de dengue o malaria con 3-4 semanas de anticipación. La propuesta combina
datos epidemiológicos, climáticos y geoespaciales para priorizar acciones
preventivas.

## Estado actual

El proyecto se encuentra en la **Fase 1: infraestructura base**. Actualmente
incluye:

- especificación funcional y no funcional;
- diseño de arquitectura, modelo de datos y API propuesta;
- backlog técnico dividido por fases;
- estructura inicial del backend con FastAPI;
- endpoint local `GET /health`.

Todavía no están implementados la conexión a PostgreSQL/PostGIS, las
migraciones Alembic, los conectores ETL, el pipeline de predicción, la
autenticación, el dashboard ni el despliegue. Las métricas de precisión y
anticipación son objetivos de diseño y no resultados validados.

## Documentación

Lectura recomendada:

1. [`../docs/product_goal.md`](../docs/product_goal.md): objetivo del producto y valor esperado.
2. [`requirements.md`](./requirements.md): requisitos funcionales y no funcionales.
3. [`design.md`](./design.md): arquitectura, modelo de datos y decisiones de diseño.
4. [`tasks.md`](./tasks.md): plan de implementación y criterios de verificación.
5. [`CONTEXT.md`](./CONTEXT.md): estado de trabajo y decisiones pendientes.
6. [`../docs/priorizacion_casos.md`](../docs/priorizacion_casos.md): priorización del caso de uso.
7. [`../docs/team_charter.md`](../docs/team_charter.md): integrantes y acuerdos del equipo.
8. [`../docs/reglas_calidad_datos.md`](../docs/reglas_calidad_datos.md): validación, limpieza e imputación.
9. [`../docs/controles_seguridad.md`](../docs/controles_seguridad.md): controles, estado y evidencia de seguridad.
10. [`../docs/eda_inicial.md`](../docs/eda_inicial.md): análisis exploratorio sobre datos reales de SENAMHI y del Ministerio de Salud.
11. [`../docs/c4/`](../docs/c4/): diagramas C4 de Contexto y Contenedores.

## Tecnología propuesta

- **Backend:** Python 3.12 y FastAPI.
- **Base de datos:** PostgreSQL 16 con PostGIS.
- **ML:** scikit-learn, XGBoost y SHAP.
- **Frontend:** React con Leaflet o Mapbox; aún no incluido.
- **Despliegue:** Railway; aún no configurado.

## Reproducir el avance actual

### Requisitos

- Git.
- Python 3.12 o una versión compatible con las dependencias fijadas en
  `requirements.txt`.

PostgreSQL/PostGIS no es necesario para ejecutar el endpoint disponible en
esta etapa.

### Instalación

Desde la raíz del repositorio:

```bash
cd dengue-malaria-prediccion
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En Windows, la activación del entorno es:

```powershell
.venv\Scripts\Activate.ps1
```

El archivo `.env.example` documenta las variables previstas para las fases
posteriores. El endpoint actual no necesita una base de datos ni secretos.

### Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

En otra terminal:

```bash
curl http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

La documentación interactiva generada por FastAPI queda disponible en
`http://127.0.0.1:8000/docs`.

### Verificaciones disponibles

```bash
python -m compileall -q app tests
pytest
```

En el estado actual, `pytest` no contiene casos de prueba y puede informar
que no se recolectaron pruebas. Los comandos de base de datos y migraciones
serán reproducibles después de completar TASK-002 y TASK-005.

## Estructura actual

```text
dengue-malaria-prediccion/
├── app/
│   ├── main.py             # aplicación FastAPI y endpoint /health
│   ├── api/routes/         # reservado para rutas REST
│   ├── core/               # reservado para configuración y seguridad
│   ├── etl/conectores/     # reservado para ingesta y limpieza
│   ├── ml/                 # reservado para predicción y explicabilidad
│   ├── models/             # reservado para modelos ORM
│   └── schemas/            # reservado para esquemas Pydantic
├── tests/                  # estructura inicial, todavía sin casos
├── requirements.txt
├── requirements.md
├── design.md
├── tasks.md
└── CONTEXT.md
```

La estructura objetivo completa, incluidos los archivos todavía pendientes,
se encuentra en [`design.md` §9](./design.md#9-estructura-de-archivos-backend).

## Decisiones y límites

- No se almacenarán datos personales de pacientes: la información
  epidemiológica se trabajará agregada por municipio y fecha (REQ-020).
- El sistema será una herramienta de apoyo; no reemplazará el criterio
  clínico ni epidemiológico.
- Toda cifra de desempeño debe identificarse como objetivo o estimación hasta
  validarse con datos reales de la zona piloto.
- Las fuentes climática (SENAMHI) y epidemiológica (Ministerio de Salud y
  Deportes, Boletín Epidemiológico N.º 13) ya están confirmadas y en uso
  para el EDA y el pipeline de datos (ver `../docs/eda_inicial.md` y
  `../docs/pipeline_datos.md`). La zona piloto definitiva para validar
  NFR-001/NFR-002 aún no está confirmada oficialmente; los cuatro
  municipios con cruce de datos real (Guayaramerín, Ixiamas, Palos Blancos,
  San Buenaventura) son la referencia usada hasta ahora.

## Flujo de trabajo

Cada integrante trabaja en su propia rama. Antes de integrar cambios se debe
comprobar que la documentación sea consistente, que el backend compile y que
las verificaciones disponibles finalicen sin errores atribuibles al cambio.
