# Guía: poner todo en marcha y probarlo desde cero

Pasos para una laptop **sin nada instalado del proyecto** (por ejemplo la segunda laptop del Plan B). Cada comando se probó el 2026-10-26 sobre un clon limpio de `main`, con un entorno de Python y una base de datos nuevos: **500 pruebas de backend, 173 de frontend, cobertura de 79,87 % y la prueba de humo, todo en verde.**

Todo se ejecuta en la terminal (Mac o Linux). Las contraseñas y claves de abajo son ejemplos: elige las tuyas, y el archivo `.env` nunca se sube a git.

## 0. Requisitos (una sola vez)

| Programa | Para qué | Comprobar |
|---|---|---|
| Git | bajar el código | `git --version` |
| Python **3.12** | la API y las pruebas | `python3.12 --version` |
| Node **22 o superior** | la interfaz | `node --version` |
| Docker | la base de datos con PostGIS | `docker --version` |

En Mac con Homebrew: `brew install git python@3.12 node`. Para Docker, Docker Desktop, o sin él: `brew install colima docker docker-compose` y luego `colima start --cpu 4 --memory 6 --disk 40`. Docker tiene que estar **encendido** antes del paso 3.

> La imagen de la base (`postgis/postgis:16-3.4`) solo existe para amd64: en un Mac con Apple Silicon corre emulada. Funciona, un poco más lenta, y Docker avisa de la diferencia de plataforma.

## 1. Bajar el código

```bash
git clone https://github.com/IvonneCM/Taller-de-Sistemas-Inteligentes.git
cd Taller-de-Sistemas-Inteligentes/dengue-malaria-prediccion
git log -1 --oneline    # debe mostrar el último commit de main
```

Para defender exactamente la versión congelada: `git checkout v0.2-mvp`.

## 2. Variables de entorno

```bash
cp .env.example .env
```

Abre `.env` y cambia **solo estas líneas** (usa tus propios valores; la clave de la base debe ser la misma en `DATABASE_URL` y en `POSTGRES_PASSWORD`):

```
DATABASE_URL=postgresql://postgres:MI-CLAVE-DB@localhost:5433/dengue_malaria
POSTGRES_PASSWORD=MI-CLAVE-DB
SECRET_KEY=una-clave-larga-y-aleatoria-de-mas-de-32-caracteres
SEED_DEMO_PASSWORD=MI-CLAVE-DE-DEMO
```

Si el puerto 5433 está ocupado, cambia `5433` por otro en `DATABASE_URL` y en `POSTGRES_HOST_PORT`.

## 3. Base de datos

```bash
docker compose up -d db
docker compose ps db        # espera hasta que diga "healthy"
```

## 4. Entorno de Python y dependencias

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Tarda unos minutos (incluye el modelo de predicción y las pruebas). Cada terminal nueva necesita `source .venv/bin/activate`, y para que lea el `.env` también:

```bash
set -a && . ./.env && set +a
```

## 5. Crear las tablas y cargar la demo

```bash
alembic upgrade head
python -m app.etl.seed_demo --todos-los-municipios --fecha 2026-03-30
```

Debe terminar mostrando 5 usuarios demo creados, 28 predicciones insertadas y 3 alertas emitidas. Los usuarios son `autoridad@`, `sedes@`, `epidemiologo@`, `coordinador@` y `admin@` seguidos de `demo.local`, todos con `SEED_DEMO_PASSWORD`.

## 6. Todas las pruebas

Con el entorno activo y el `.env` cargado (pasos 4 y 5):

| # | Qué prueba | Comando | Debe salir |
|---|---|---|---|
| 1 | Migraciones al día | `alembic check` | `No new upgrade operations detected.` |
| 2 | Backend completo | `python -m pytest -q -p no:warnings` | `500 passed` (tarda unos 2 minutos) |
| 3 | Cobertura mínima de 70 % en ingesta, limpieza y predicción | `python -m pytest tests/etl tests/ml -q -p no:warnings --cov=app/etl --cov=app/ml --cov-fail-under=70` | `Required test coverage of 70% reached` (cerca de 80 %) |
| 4 | Flujo extremo a extremo | `python -m pytest tests/e2e -q -p no:warnings` | `9 passed` |
| 5 | Controles de seguridad | `python -m app.core.revision_seguridad` | `6 OK, 0 con falla` (el de HTTPS solo se comprueba con `--url`) |
| 6 | Interfaz | `cd frontend && npm ci && npx vitest run && npm run build` | `173 passed` y `built` |

**Las pruebas son seguras con la demo cargada:** cada una trabaja dentro de una transacción que se deshace, así que no borran la demo.

### Pruebas que se saltan sin una base exclusiva (opcional)

Sin lo siguiente, en la prueba 2 aparecen unas 45 pruebas como `skipped` (las de alertas vigentes y priorización de campañas). Para correrlas también, crea una base exclusiva con este nombre exacto:

```bash
docker compose exec -T db psql -U postgres -c "CREATE DATABASE gatobyte_task024025_test"
docker compose exec -T db psql -U postgres -d gatobyte_task024025_test -c "CREATE EXTENSION IF NOT EXISTS postgis"
export GATOBYTE_TEST_DATABASE_URL="postgresql://postgres:MI-CLAVE-DB@localhost:5433/gatobyte_task024025_test"
DATABASE_URL=$GATOBYTE_TEST_DATABASE_URL alembic upgrade head
python -m pytest -q -p no:warnings
```

Con eso la prueba 2 corre **sin ninguna omitida** y da `500 passed`.

## 7. Levantar el sistema para mostrarlo

Necesitas **dos terminales**, las dos dentro de `dengue-malaria-prediccion`.

**Terminal 1: la API** (con el entorno activo y el `.env` cargado):

```bash
uvicorn app.main:app --port 8000
```

**Terminal 2: la interfaz:**

```bash
cd frontend && npm run dev
```

Abre http://localhost:5173 y entra con `epidemiologo@demo.local` y `SEED_DEMO_PASSWORD`.

**Prueba de humo** (con la API encendida), para comprobar antes de empezar:

```bash
SMOKE_URL=http://localhost:8000 SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py
```

Debe terminar con `RESULTADO: todo correcto`.

*Variante con todo en Docker:* `docker compose up -d --build api web` y la interfaz queda en http://localhost:8080 (la API en :8000), con la humo apuntando a `http://localhost:8080/api`.

## 8. Qué mostrar y en qué orden

El guion completo, con minutos y respuestas a preguntas probables, está en `docs/guion_demo_y_plan_b.md`. Resumen de lo que se ve:

1. **Terminal:** las pruebas de la sección 6 (la 2 y la 6 son las que se ven en vivo).
2. **Entrar como `autoridad@demo.local`:** el Resumen y el Mapa, con el aviso de que no hay predicción de malaria.
3. **Salir y entrar como `epidemiologo@demo.local`:** aparece «Qué influyó en esta predicción» y la pestaña Historial. Es el mismo dato con otra respuesta desde el servidor.
4. **Pestaña Alertas:** las 3 alertas, cada una con su justificación.
5. **Terminal, errores controlados:** `curl -s -X POST localhost:8000/auth/login -d "username=x"` responde 422 sin devolver lo enviado; y 6 intentos fallidos de login seguidos responden 429.
6. **Terminal, estado de la API:** `curl -i localhost:8000/health/ready` responde 200 con la base conectada.

## 9. Si algo falla

| Síntoma | Causa y solución |
|---|---|
| `No module named 'sqlalchemy'` o `No module named pytest` | El entorno no está activo o faltan las dependencias: `source .venv/bin/activate && pip install -r requirements.txt` |
| `connection refused` al migrar | La base no está encendida: `docker compose up -d db` y esperar a `healthy` |
| `password authentication failed` | La clave de `DATABASE_URL` no coincide con la de `POSTGRES_PASSWORD`. Si ya habías creado la base con otra clave: `docker compose down -v` y volver al paso 3 |
| `port is already allocated` | El puerto 5433 está ocupado: cambiar el puerto en `.env` (paso 2) |
| El login da 503 o `/health/ready` da 503 | La base no responde, o `DATABASE_URL` apunta a otro lugar |
| `SECRET_KEY` rechazada | Debe tener al menos 32 caracteres |
| Una prueba falla y no sabes por qué | Copia las últimas 25 líneas de `python -m pytest -q -p no:warnings 2>&1 | tail -25` |
| Quieres rehacer todo desde cero | `docker compose down -v`, y de nuevo desde el paso 3 |
