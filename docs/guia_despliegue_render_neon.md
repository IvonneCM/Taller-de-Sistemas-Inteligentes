# Guía de despliegue: Render + Neon + GitHub Actions (TASK-004)

**Arquitectura:** la API (imagen `api` del `Dockerfile`) corre en un servicio web
gratuito de Render; la base PostgreSQL + PostGIS vive en Neon; el job semanal de
predicción (TASK-016) se ejecuta con un workflow programado de GitHub Actions.
Los tres se conectan solo por variables de entorno.

## 0. Requisitos previos

- Una cuenta de GitHub con acceso al repositorio
  `IvonneCM/Taller-de-Sistemas-Inteligentes` (o un fork), una cuenta de Render y
  una cuenta de Neon. Ninguna pide tarjeta para el plan gratuito
- Una clave secreta para producción, que se genera con el comando siguiente y se
  guarda en un gestor de contraseñas, nunca en el repositorio:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 1. Base de datos en Neon

1. En Neon se crea un proyecto nuevo con PostgreSQL 16 y una región cercana a la de
   Render (para reducir la latencia entre ambos).
2. En el **SQL Editor** del proyecto se activa PostGIS, una sola vez:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Version();
```

3. En **Connection Details** se copia la cadena de conexión **directa** (sin
   `-pooler` en el host). Tiene la forma
   `postgresql://usuario:clave@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`.
   Esa cadena es el valor de `DATABASE_URL` en los pasos siguientes. Se usa la
   directa porque la conexión con pooler (PgBouncer) puede dar problemas con las
   migraciones de Alembic **[Verificar]**.
4. Neon suspende el cómputo tras unos 5 minutos sin uso y lo reactiva en la
   siguiente consulta, con una demora de algunos segundos. La aplicación ya usa
   `pool_pre_ping`, que descarta las conexiones caídas.

## 2. API en Render

1. En Render se elige **New** y **Web Service**, se conecta el repositorio de
   GitHub y se selecciona la rama que se desplegará (por ejemplo `main`).
2. Configuración del servicio:

| Campo | Valor |
|---|---|
| Language | Docker |
| Root Directory | `dengue-malaria-prediccion` |
| Dockerfile Path | `./dengue-malaria-prediccion/Dockerfile`. Render define este campo como la ruta al Dockerfile **relativa a la raíz del repositorio** (por defecto `./Dockerfile`), de modo que debe incluir el directorio del backend. |
| Instance Type | Free |
| Docker Command | `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'"` (puede estar en la sección **Advanced**) |

   El contexto de construcción de Docker debe ser `dengue-malaria-prediccion`,
   porque el `Dockerfile` copia `app/`, `alembic/` y los `requirements-*.txt` desde
   ese directorio. Tanto **Dockerfile Path** como **Docker Build Context
   Directory** son relativos a la raíz del repositorio. Dockerfile Path debe
   terminar en el nombre del archivo: `dengue-malaria-prediccion/Dockerfile`.

   En la sección **Advanced** del formulario también figuran, y se dejan así:

   | Campo | Valor |
   |---|---|
   | Health Check Path | `/health` |
   | Auto-Deploy | On Commit |
   | Docker Build Context Directory | `dengue-malaria-prediccion` |
   | Pre-Deploy Command | vacío (las migraciones van en el Docker Command) |

   El **Pre-Deploy Command** de Render sería la ubicación natural de
   `alembic upgrade head`, pero no se confirmó que esté disponible en el plan
   gratuito **[Verificar]**; por eso la migración va en el Docker Command, que
   funciona en cualquier plan.

3. En **Environment** se definen:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | La cadena directa de Neon del paso 1.3 |
| `SECRET_KEY` | La clave generada en el paso 0 (más de 32 caracteres) |
| `ENVIRONMENT` | `production` |

   `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` y `REFRESH_TOKEN_EXPIRE_DAYS` tienen
   valores por defecto. Con `ENVIRONMENT=production`, la API se niega a arrancar si
   `SECRET_KEY` es la de ejemplo o tiene menos de 32 caracteres. Render asigna el
   puerto mediante `PORT`, que el comando anterior ya usa.
4. Se crea el servicio. Render construye la imagen, la despliega y ofrece una URL
   pública con HTTPS del tipo `https://<nombre>.onrender.com`.

## 3. Verificar (cierre de TASK-004)

```powershell
curl https://<nombre>.onrender.com/health
```

La respuesta esperada es `{"status":"ok"}` con código 200. La primera petición
después de un periodo de inactividad puede tardar cerca de un minuto, porque el
servicio gratuito se duerme. Una vez obtenida la respuesta:

- se anotan la URL y la fecha en `tasks.md` (TASK-004) y se marca la tarea `[x]`;
- se adjunta la salida del `curl` como evidencia;
- se actualiza la fila de HTTPS de `docs/controles_seguridad.md`;
- se actualizan el ADR-003 y `design.md` §1, porque el proveedor deja de ser Railway.

## 4. Cargar el catálogo inicial

Tras el primer despliegue las tablas existen, pero están vacías. Neon admite
conexiones externas, de modo que el script de catálogo se ejecuta desde una máquina
del equipo, desde `dengue-malaria-prediccion/` y con el entorno virtual activado:

```powershell
$env:DATABASE_URL = "<cadena directa de Neon>"
$env:SECRET_KEY = "cualquier-valor-local"
python -m app.etl.seed_catalogo
Remove-Item Env:DATABASE_URL, Env:SECRET_KEY
```

El script es idempotente. Todavía no existe un script que cargue en la base los CSV
de casos y clima, y la tabla `roles` sigue vacía (la necesitan TASK-017 y
TASK-018). Ninguna de las dos carencias afecta a `/health`.

## 5. Evitar que la API se duerma antes de una demostración

El servicio gratuito de Render se suspende tras 15 minutos sin tráfico. Hay dos
formas de manejarlo:

- **Despertarlo a mano** con `curl .../health` unos minutos antes de la
  presentación.
- **Mantenerlo activo** con un monitor externo gratuito que consulte `/health` cada
  5 a 10 minutos. Un servicio siempre activo consume unas 744 horas al mes y el
  límite gratuito es de 750 horas por espacio de trabajo, por lo que solo cabe un
  servicio gratuito encendido todo el mes.

## 6. Job semanal con GitHub Actions (diseño; TASK-016)

No se debe agregar este archivo al repositorio hasta que exista
`app/ml/prediccion.py` (TASK-014): un workflow que invoque un módulo inexistente
fallaría cada semana. Cuando exista, el archivo sería
`.github/workflows/prediccion_semanal.yml`:

```yaml
name: Prediccion semanal

on:
  schedule:
    - cron: "17 6 * * 1"   # lunes 06:17 UTC = 02:17 en Bolivia (UTC-4)
  workflow_dispatch:        # ejecucion manual, tambien sirve para la verificacion de TASK-016

jobs:
  predecir:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: dengue-malaria-prediccion
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: dengue-malaria-prediccion/requirements-ml.txt
      - run: pip install -r requirements-ml.txt
      - run: python -m app.ml.prediccion
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          ENVIRONMENT: production
```

Las variables `DATABASE_URL` y `SECRET_KEY` se registran en el repositorio, en
**Settings**, **Secrets and variables**, **Actions**. Cuatro precauciones:

- El minuto `17` evita la hora en punto, cuando GitHub tiene más carga y puede
  retrasar o descartar ejecuciones programadas.
- GitHub [desactiva las ejecuciones programadas tras 60 días sin actividad](https://dev.to/gautamkrishnar/how-to-prevent-github-from-suspending-your-cronjob-based-triggers-knf)
  en el repositorio, sin avisar. Un push o la ejecución manual lo reactivan.
  **[Verificar]** si aplica también a repositorios privados y cuántos minutos
  gratuitos ofrece la cuenta.
- La instalación de `xgboost` descarga cerca de 470 MB de librerías de GPU que no se
  usan; la caché de pip la acelera a partir de la segunda ejecución.
- Sigue sin resolverse cómo llega el modelo entrenado en Colab al job. Una opción
  es publicarlo como release del repositorio y descargarlo en un paso previo del
  workflow.

## 7. Solución de problemas

| Síntoma | Causa probable |
|---|---|
| El despliegue falla al arrancar con un error de `alembic` | `DATABASE_URL` incorrecta, o PostGIS no activado en Neon (paso 1.2). Se revisan los logs de Render. |
| La API no arranca por `SECRET_KEY` | La variable falta, es la de ejemplo o tiene menos de 32 caracteres. |
| `/health` tarda más de un minuto | El servicio estaba dormido; es el comportamiento esperado del plan gratuito. |
| Error de SSL al conectar con Neon | La cadena no incluye `?sslmode=require`. |
| `Dockerfile` no encontrado | Ruta incorrecta en Dockerfile Path o Root Directory (paso 2.2). |

## 8. Desventajas conocidas

- La API gratuita se duerme y tarda cerca de un minuto en responder tras la
  inactividad.
- Neon gratuito ofrece del orden de 0,5 GB y suspende el cómputo sin uso. Las
  fuentes consultadas discrepan sobre sus horas de cómputo mensuales y sobre qué
  ocurre al superarlas **[Verificar]** en su página de precios.
- Los cron jobs propios de Render son de pago, de ahí el uso de GitHub Actions. Las
  ejecuciones programadas de Actions pueden retrasarse, y el cómputo del job corre
  en un servidor aparte, por lo que la base debe aceptar conexiones externas.
- Render gratuito no permite discos persistentes, lo cual no afecta a esta
  arquitectura porque los datos viven en Neon.
- Hay tres proveedores y tres paneles que mantener, con secretos repartidos entre
  Render y GitHub.
- Cada push a la rama conectada despliega directamente a producción.
- No hay copias de seguridad garantizadas: conviene hacer `pg_dump` periódicos
  contra Neon.
- El frontend no está cubierto en esta guía.
