# Sistema de Predicción Temprana de Brotes de Dengue/Malaria

> **Backend en desarrollo incremental.** Esta carpeta contiene la
> especificación, el diseño y la implementación del backend (FastAPI +
> PostgreSQL/PostGIS). Ya están cerrados el baseline XGBoost con SHAP
> (TASK-012/013) y la autenticación JWT con RBAC (TASK-017/018). El
> trabajo de datos (EDA, calidad, pipeline, línea base) vive en
> `../docs/`, `../scripts/` y `../data/`, en la raíz del repositorio.
> Ver `tasks.md` y `CONTEXT.md` para el estado exacto.

Proyecto universitario orientado a apoyar a SEDES, autoridades de salud y
coordinadores municipales en la identificación de zonas con riesgo de brotes
de dengue o malaria con 3-4 semanas de anticipación. La propuesta combina
datos epidemiológicos, climáticos y geoespaciales para priorizar acciones
preventivas.

## Estado actual

Este proyecto tiene dos frentes de trabajo con avance muy distinto, que
conviene no confundir:

**Backend (este directorio) — avance incremental.**
Incluye la especificación funcional y no funcional, el diseño de
arquitectura, el modelo de datos y el backlog técnico. Ya están
implementados la conexión a PostgreSQL/PostGIS, las migraciones Alembic,
los conectores ETL formales, el baseline XGBoost con explicabilidad SHAP y
la autenticación JWT con RBAC. Todavía faltan los endpoints de datos, el
pipeline de predicción completo y el dashboard. Ver `CONTEXT.md` para el
estado exacto y las decisiones pendientes.

**Datos (`../scripts/`, `../data/`, `../docs/`):** más avanzado que el
backend. Ya existe ingesta real (no sintética) de SENAMHI y del Ministerio
de Salud y Deportes de Bolivia, un EDA completo sobre esos datos, reglas de
calidad/imputación documentadas, y un prototipo de pipeline de limpieza que
las implementa (ver `../docs/eda_inicial.md` y `../docs/cierre_sprint1.md`).
Este trabajo todavía no está integrado al backend — los conectores de
`app/etl/` (TASK-008/009/010 en `tasks.md`) deben reutilizar esa lógica en
vez de rediseñarla desde cero.

Las métricas de precisión y anticipación del modelo (NFR-001, NFR-002)
siguen siendo objetivos de diseño, no resultados validados: no existe
todavía un motor de predicción entrenado (ver `../docs/metricas_valor.md`).

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
12. [`../docs/metricas_valor.md`](../docs/metricas_valor.md): métricas de valor y criterios de éxito.
13. [`../docs/cierre_sprint1.md`](../docs/cierre_sprint1.md): backlog pendiente, bloqueos y próximos pasos.
14. [`../docs/pipeline_datos.md`](../docs/pipeline_datos.md): pipeline reproducible de limpieza e imputación (Línea Base — Paso 2).
15. [`../docs/privacidad_datos.md`](../docs/privacidad_datos.md): restricciones de privacidad y licencias de datos.
16. [`../docs/entorno_datos_iniciales.md`](../docs/entorno_datos_iniciales.md): entorno reproducible y estado inicial de los datos (Línea Base — Paso 1).
17. [`../docs/linea_base.md`](../docs/linea_base.md): línea base y registro de experimentos (Línea Base — Paso 3).
18. [`../docs/inventario_datos.md`](../docs/inventario_datos.md): inventario de fuentes de datos epidemiológicos y climáticos.
19. [`../docs/adr/`](../docs/adr/): registro de decisiones de arquitectura (ADR).
20. [`../docs/risk_register.md`](../docs/risk_register.md): Risk Register inicial.
21. [`../docs/declaracion_uso_ia.md`](../docs/declaracion_uso_ia.md): declaración de uso de IA y revisión humana.

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

PostgreSQL 16 con PostGIS es necesario para autenticación, migraciones y
las pruebas de API. Para desarrollo local se puede levantar con Docker.

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

El archivo `.env.example` documenta las variables necesarias. Copiarlo como
`.env` y completar `DATABASE_URL`, `SECRET_KEY` y `SEED_DEMO_PASSWORD`. El
archivo `.env` está ignorado por Git y nunca debe commitearse.

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

### Base de datos local y usuarios demo

Levantar PostGIS en Docker (puerto local `55432` para no chocar con un
PostgreSQL ya instalado):

```powershell
docker run --name dengue-postgis-local `
  -e POSTGRES_PASSWORD=test `
  -e POSTGRES_DB=dengue_malaria `
  -p 55432:5432 `
  -d postgis/postgis:16-3.4

docker exec dengue-postgis-local psql -U postgres -d dengue_malaria `
  -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Definir las variables y aplicar migraciones:

```powershell
$env:DATABASE_URL="postgresql://postgres:test@localhost:55432/dengue_malaria"
$env:SECRET_KEY="cambiar-por-una-clave-larga-y-aleatoria"
$env:ENVIRONMENT="development"
$env:SEED_DEMO_PASSWORD="elegir-una-clave-local-de-al-menos-8-caracteres"

.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.etl.seed_catalogo
.\.venv\Scripts\python.exe -m app.etl.seed_usuarios
```

El seed crea estos usuarios ficticios (`@demo.local`), todos con la
contraseña de `SEED_DEMO_PASSWORD`:

| Email | Rol |
|---|---|
| `autoridad@demo.local` | `autoridad` |
| `sedes@demo.local` | `sedes` |
| `epidemiologo@demo.local` | `epidemiologo` |
| `coordinador@demo.local` | `coordinador_municipal` |
| `admin@demo.local` | `admin` |

No se commitea ninguna contraseña. Para borrar únicamente esos usuarios y
sus refresh tokens:

```powershell
.\.venv\Scripts\python.exe -m app.etl.seed_usuarios --delete
```

### Verificaciones disponibles

```bash
python -m compileall -q app tests
pytest tests/api -q
pytest tests/ml -q
alembic check
```

Los tests de API necesitan `DATABASE_URL` apuntando a una base con las
migraciones aplicadas. Los fixtures crean sus usuarios dentro de una
transacción y revierten los cambios al terminar.

## Estructura actual

Estructura de `dengue-malaria-prediccion/` (el backend):

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

Estructura del repositorio completo (raíz), donde vive el trabajo de datos:

```text
Taller-de-Sistemas-Inteligentes/
├── dengue-malaria-prediccion/   # backend FastAPI (este directorio)
├── docs/                        # documentación del equipo (product_goal,
│                                 # EDA, reglas de calidad, C4, métricas...)
├── scripts/                     # ingesta y EDA reales: descargar_senamhi.py,
│                                 # procesar_clima.py, eda_*.py, integrar_datos.py
├── data/
│   ├── raw/                     # datos crudos (parte versionada con DVC)
│   └── processed/                # datos ya limpios/agregados
└── requirements.txt              # dependencias del código de datos/EDA
```

## Decisiones y límites

- No se almacenarán datos personales de pacientes: la información
  epidemiológica se trabajará agregada por municipio y fecha (REQ-020).
- El sistema será una herramienta de apoyo; no reemplazará el criterio
  clínico ni epidemiológico.
- Toda cifra de desempeño debe identificarse como objetivo o estimación hasta
  validarse con datos reales de la zona piloto.
- Las fuentes climática (SENAMHI) y epidemiológica (Ministerio de Salud y
  Deportes, Boletín Epidemiológico N.º 13) ya están confirmadas y en uso
  para el EDA (ver `../docs/eda_inicial.md`). La zona piloto definitiva para
  validar NFR-001/NFR-002 aún no está confirmada oficialmente; los cuatro
  municipios con cruce de datos real (Guayaramerín, Ixiamas, Palos Blancos,
  San Buenaventura) son la referencia usada hasta ahora (ver `design.md` §10).

## Estado del desarrollo del backend

El backend ya está en desarrollo activo. El orden de trabajo y las tareas
pendientes están en `tasks.md`; el estado de la última sesión, las
decisiones tomadas y los bloqueos están en `CONTEXT.md`. Los conectores de
ingesta y limpieza (TASK-008/009/010) deben reutilizar la lógica ya
construida y verificada en `../scripts/` y `../docs/pipeline_datos.md`, no
rediseñarla desde cero. Ver `../docs/cierre_sprint1.md` para el backlog de
datos.

## Flujo de trabajo

Cada integrante trabaja en su propia rama. Antes de integrar cambios se debe
comprobar que la documentación sea consistente, que el backend compile y que
las verificaciones disponibles finalicen sin errores atribuibles al cambio.
