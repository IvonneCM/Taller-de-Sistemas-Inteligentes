# Sistema de Predicción Temprana de Brotes de Dengue/Malaria

> **MVP integrado (2.ª defensa).** Esta carpeta contiene la especificación, el
> diseño y la implementación del sistema: API FastAPI + PostgreSQL/PostGIS,
> modelo XGBoost con SHAP e interfaz React. El pipeline de datos (EDA, calidad,
> DVC) vive en `../docs/`, `../scripts/` y `../data/`, en la raíz del
> repositorio. Ver `tasks.md` y `CONTEXT.md` para el estado exacto.

Proyecto universitario orientado a apoyar a SEDES, autoridades de salud y
coordinadores municipales en la identificación de zonas con riesgo de brotes
de dengue o malaria con 3-4 semanas de anticipación. La propuesta combina
datos epidemiológicos, climáticos y geoespaciales para priorizar acciones
preventivas.

## Estado actual

**Recorrido completo y reproducible:** datos reales del Boletín Epidemiológico
N.º 13 (pipeline DVC en `../scripts/`) → ingesta (`app/etl/`) → base
PostgreSQL/PostGIS → modelo XGBoost con explicabilidad SHAP (`app/ml/`) → API
FastAPI con login JWT y control de acceso por rol → interfaz web React con mapa
(`frontend/`). La demo cubre los 42 municipios con casos del boletín: 28 con
dengue y 21 con malaria
([ADR-007](../docs/adr/ADR-007-catalogo-ampliado-opcional.md)).

- **Dengue:** predicciones a 3 semanas y alertas con su justificación.
- **Malaria:** casos observados, sin modelo: la fuente solo trae acumulados
  ([ADR-005](../docs/adr/ADR-005-malaria-acumulado-en-bd.md)).
- **Boletines nuevos:** el sitio del Ministerio bloquea la descarga automática;
  una persona sube el PDF en la pestaña Datos y el sistema lo verifica contra
  los totales impresos antes de guardar (`POST /admin/boletines`).
- **Despliegue:** API en Render y base en Neon
  ([ADR-006](../docs/adr/ADR-006-despliegue-render-neon.md)); predicción
  semanal en GitHub Actions. La interfaz todavía no está publicada y la base
  de Neon no tiene los datos de demo (riesgo M-10).

Para recorrerlo y defenderlo paso a paso, ver
[`../docs/guion_demo_y_plan_b.md`](../docs/guion_demo_y_plan_b.md); la arquitectura
real está en [`../docs/arquitectura_actual.md`](../docs/arquitectura_actual.md).
Falta la validación retrospectiva (TASK-034), que necesita una fuente de brotes
confirmados (riesgo M-08).

Las métricas de precisión y anticipación del modelo (NFR-001, NFR-002)
siguen siendo objetivos de diseño, no resultados validados: existe un modelo de
referencia entrenado, pero con 13 semanas de datos **no supera de forma
concluyente a una regla simple** (ver `../docs/resultados_experimentales.md`).

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
22. [`../docs/arquitectura_actual.md`](../docs/arquitectura_actual.md): arquitectura real del MVP (código, configuración y secretos).
23. [`../docs/contrato_api.md`](../docs/contrato_api.md): endpoints, roles y formato de errores.
24. [`../docs/resultados_experimentales.md`](../docs/resultados_experimentales.md): resultados contra la línea base, con los intentos fallidos.
25. [`../docs/guion_demo_y_plan_b.md`](../docs/guion_demo_y_plan_b.md): guion de la demostración y Plan B.
26. [`../docs/revision_seguridad.md`](../docs/revision_seguridad.md): revisión de seguridad con evidencia, hallazgos y firma.

## Tecnología

- **Backend:** Python 3.12 y FastAPI.
- **Base de datos:** PostgreSQL 16 con PostGIS.
- **ML:** scikit-learn, XGBoost y SHAP.
- **Frontend:** React 19 + Vite + Leaflet (`frontend/`).
- **Despliegue:** Render (API) + Neon (PostgreSQL/PostGIS) y GitHub Actions para la predicción semanal (TASK-004, ADR-006). `Dockerfile` y `docker-compose.yml` funcionan en local.

## Reproducir el avance actual

### Requisitos

- Git.
- Python 3.12 (la versión fijada en el `Dockerfile`) o una compatible con las
  dependencias de `requirements.txt`.
- Docker, para la base de datos PostgreSQL + PostGIS.

El endpoint `/health` no necesita base de datos, pero `pytest`, `alembic` y los
conectores ETL sí.
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

### Configuración

```bash
cp .env.example .env     # y reemplazar los marcadores "cambiar-..." por valores propios
docker compose up -d db  # PostgreSQL 16 + PostGIS en el puerto 5433
alembic upgrade head
```

`app/core/config.py` lee `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` y `ENVIRONMENT` del
entorno o de `.env`. `DATABASE_URL` y `SECRET_KEY` son obligatorias: sin ellas
la aplicación no arranca. `docker compose up --build` levanta además la API en
`http://localhost:8000`.

Imágenes de Docker (un solo `Dockerfile` con dos targets, más el del frontend):

| Servicio | Imagen | Tamaño | Comando |
|---|---|---|---|
| `api` | target `api` (incluye pdfplumber para leer boletines) | 417 MB | `docker compose up --build api` |
| `web` | `frontend/Dockerfile` (nginx) | 74 MB | `docker compose up --build api web` → http://localhost:8080 |
| `ml` | target `ml` (pandas, xgboost, shap) | 2,3 GB | `docker compose run --rm ml python -m <modulo>` |

**Interfaz completa con Docker, desde un clon limpio** (`.env` ya copiado de
`.env.example`):

```bash
docker compose up -d --build api web     # la API crea las tablas sola (RUN_MIGRATIONS=1)
docker compose run --rm -e SEED_DEMO_PASSWORD='<clave-de-demo>' ml python -m app.etl.seed_demo --todos-los-municipios --fecha 2026-03-30
# abrir http://localhost:8080 y entrar con epidemiologo@demo.local (o autoridad@, sedes@, coordinador@, admin@)
```

Sin el segundo comando la interfaz carga, pero la base está vacía y no hay
usuarios para entrar. El servicio `ml` monta `../data` en `/data` (solo lectura)
porque los CSV procesados no van dentro de la imagen.

El `frontend/` es solo un esqueleto (mapa base y comprobación de `/health`); no
implementa las vistas de TASK-027 a 031. La imagen `ml` pesa más porque
`xgboost` incluye librerías de GPU de NVIDIA (unos 470 MB) que no se usan en CPU;
la imagen `api` no las lleva.
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

### Demostración de punta a punta (datos reales)

Con la base y las variables del paso anterior, **un comando** carga los casos
reales del boletín, registra el modelo, genera las predicciones y crea los cinco
usuarios demo (`SEED_DEMO_PASSWORD` es obligatoria):

```bash
python -m app.etl.seed_demo --todos-los-municipios --fecha 2026-03-30   # idempotente; sin la primera opción, solo la zona piloto de 4
uvicorn app.main:app --port 8000
SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py
```

No carga predicciones de malaria (no hay modelo) ni brotes confirmados: no
existen esas fuentes. Las alertas las crea `evaluacion_alertas` con el umbral
vigente (70 % por defecto), así que hoy no se emite ninguna hasta que un admin lo
baje con `POST /admin/umbrales`. El script de humo (`scripts/smoke_test.py`)
sirve también contra un despliegue (`SMOKE_URL=https://…`).

### Interfaz web

```bash
cd frontend
npm ci
npm run dev          # http://localhost:5173, reenvía /api a la API local (puerto 8000)
npm run dev:render   # igual, pero reenvía /api a la URL de API_TARGET en frontend/.env.render
npm test             # pruebas de la interfaz
npm run build
```

La primera vez, `cp frontend/.env.example frontend/.env.render` y se completa la URL
de la API desplegada (el archivo está en `.gitignore`; sin él, `dev:render` falla
con un mensaje claro). Para otra URL puntual: `API_TARGET=https://otra-api.example npm run dev`. El
cambio de destino ocurre en el servidor de desarrollo de Vite (proxy), así que no
hace falta CORS. Con `dev:render` la primera petición tarda cerca de un minuto si
la API gratuita estaba dormida, y la interfaz corta a los 15 s: conviene
despertarla antes con `curl https://taller-de-sistemas-inteligentes.onrender.com/health`.
Para una compilación de producción servida desde otro origen se usa
`VITE_API_URL` (se fija al compilar) y la API necesitaría CORS, que aún no existe.

La interfaz abre en el **Resumen** (ambas enfermedades) y el selector cambia entre malaria y dengue en el mapa, las alertas y el historial. Sigue el sistema de
diseño de `frontend/src/styles/tokens.css` (fuente del sistema, modo claro y
oscuro, contraste revisado por prueba automática). El access token vive solo en
memoria; el refresh token en `sessionStorage` (ver riesgo M-11 en
`../docs/risk_register.md`).

### Revisión de seguridad

```bash
python -m app.core.revision_seguridad                             # sale con código 1 si hay una falla
python -m app.core.revision_seguridad --url https://<despliegue>  # además comprueba HTTPS
```

Verifica que no haya datos personales de pacientes, alertas sin justificación, contraseñas sin hash ni secretos versionados. El checklist, los hallazgos y la firma del equipo están en [`../docs/revision_seguridad.md`](../docs/revision_seguridad.md). Con `ENVIRONMENT=production` la API no publica `/docs` ni `/openapi.json`.

### Observabilidad y errores

Cada respuesta trae `X-Request-ID`, que también aparece en los logs de esa
petición. Una base de datos caída responde `503` (no `500`) y
`GET /health/ready` la comprueba; `GET /health` solo dice que la API vive. Los
errores nunca devuelven trazas ni lo que la persona envió. Ajustes opcionales:
`LOG_LEVEL`, `DB_CONNECT_TIMEOUT_SECONDS`, `DB_STATEMENT_TIMEOUT_MS`,
`DB_POOL_TIMEOUT_SECONDS` (ver `.env.example`).

### Verificaciones disponibles

```bash
python -m compileall -q app tests
pytest tests/api -q
pytest tests/ml -q
alembic check
```

`pytest` necesita la base de datos del paso "Configuración" y un `.env` con
`SECRET_KEY`. Estado verificado el 2026-10-26: **389 tests del backend** y
**120 de la interfaz** en verde, con 80 % de cobertura en `app/etl` y `app/ml`
(`pytest --cov=app/etl --cov=app/ml`). Los tests necesitan `DATABASE_URL`
apuntando a una base con las migraciones aplicadas. Cada test corre dentro de
una transacción que se revierte y parte de las tablas de datos vacías, así que
es seguro correrlos contra una base de desarrollo con datos de demostración. La
suite se niega a correr con `ENVIRONMENT=production`. Las 27 pruebas de integración de
TASK-024/025 (`tests/prevencion/`) se omiten salvo que `GATOBYTE_TEST_DATABASE_URL`
apunte a una base de pruebas **vacía y migrada** (no a la de desarrollo con la demo
cargada); el CI la define. El flujo completo está en
`tests/e2e/`. Hay integración continua en `.github/workflows/ci.yml`.

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
├── tests/
├── frontend/               # esqueleto React + Vite + Leaflet (Fase 5); Dockerfile propio
├── Dockerfile              # targets api y ml
├── docker-compose.yml      # db, api, web y ml (profile "jobs")
├── requirements.txt        # entorno local completo
├── requirements-api.txt    # imagen api
├── requirements-ml.txt     # imagen ml
├── requirements-dev.txt    # pytest, black, ruff
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
