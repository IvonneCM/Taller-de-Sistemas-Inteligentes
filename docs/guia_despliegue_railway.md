# Guía de despliegue en Railway (TASK-004)

**Alcance:** desplegar la API (`/health`) y la base PostgreSQL + PostGIS. No incluye
el frontend ni el job semanal de predicción (TASK-016), que quedan pendientes.

**Estado:** los archivos del repositorio están listos y probados en local; el
despliegue real y la comprobación con `curl` sobre la URL pública no se han
realizado, porque requieren la cuenta del equipo en Railway. Los nombres de los
botones del panel pueden cambiar. Los puntos marcados con **[Verificar]** no se
pudieron confirmar en la documentación y deben comprobarse en el panel.

## 0. Requisitos previos

- Una cuenta de Railway con el crédito de prueba o el plan Hobby (los costos se
  resumen en `CONTEXT.md` §9).
- Acceso de Railway al repositorio `IvonneCM/Taller-de-Sistemas-Inteligentes`.
  La persona propietaria del repositorio debe autorizar la aplicación de Railway
  en GitHub, o bien se despliega desde un fork.
- Los cambios de esta guía subidos a la rama que Railway seguirá:
  `railway.toml`, `Dockerfile` y `app/core/config.py`.
- Una clave secreta para producción, que se genera con el comando siguiente y se
  guarda en un gestor de contraseñas, nunca en el repositorio:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 1. Crear el proyecto y la base de datos

1. En Railway se elige **New Project** y luego **Empty Project**.
2. Se agrega la [plantilla PostGIS](https://railway.com/deploy/postgis) mediante
   **Add** y **Template** (PostgreSQL 16 con PostGIS 3.4, igual que el entorno
   local). No debe usarse el Postgres por defecto de Railway, porque no incluye
   PostGIS.
3. En el servicio de la base de datos se comprueba lo siguiente:
   - **[Verificar]** Que tenga un volumen asociado. Sin volumen, los datos se
     pierden al reiniciar el servicio.
   - **[Verificar]** Los nombres de sus variables en la pestaña **Variables**
     (por ejemplo `DATABASE_URL`, `DATABASE_PUBLIC_URL`, `PGHOST`, `PGUSER`,
     `PGPASSWORD`, `PGDATABASE`). La plantilla no documenta cuáles define.
4. Se confirma que PostGIS está activo en la base, desde la pestaña **Data** o con
   `psql`:

```sql
SELECT PostGIS_Version();
```

   Si la consulta falla, se ejecuta una sola vez
   `CREATE EXTENSION IF NOT EXISTS postgis;`. La migración de Alembic no crea la
   extensión.

## 2. Crear el servicio de la API

1. Se elige **Add** y **GitHub Repo**, y se selecciona el repositorio y la rama
   que se desplegará (por ejemplo `main`).
2. En **Settings** del servicio se configura:
   - **Root Directory:** `dengue-malaria-prediccion`
   - **Config File Path:** `/dengue-malaria-prediccion/railway.toml`. Este ajuste
     es obligatorio: según la
     [documentación de Railway](https://docs.railway.com/guides/monorepo), el
     archivo de configuración no sigue al Root Directory. Sin él, Railway ignora
     `railway.toml` y no ejecuta las migraciones ni el healthcheck.
   - El constructor (builder) se toma de `railway.toml`: usa el `Dockerfile` y
     Railway construye su última etapa, que es la imagen `api`.
3. En **Variables** del servicio de la API se definen:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | Referencia a la variable de la base de datos, por ejemplo `${{PostGIS.DATABASE_URL}}` (con el nombre real del servicio y de la variable obtenido en el paso 1.3). Debe ser la URL interna (`*.railway.internal`), no la pública. |
| `SECRET_KEY` | La clave generada en el paso 0 (más de 32 caracteres). |
| `ENVIRONMENT` | `production` |

   `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` y `REFRESH_TOKEN_EXPIRE_DAYS` tienen
   valores por defecto y no es necesario definirlas. Con `ENVIRONMENT=production`,
   la API se niega a arrancar si `SECRET_KEY` es la de ejemplo o tiene menos de
   32 caracteres.

   Si la base de datos no ofrece una variable `DATABASE_URL` lista, la URL se arma
   con sus partes:
   `postgresql://${{PostGIS.PGUSER}}:${{PostGIS.PGPASSWORD}}@${{PostGIS.PGHOST}}:${{PostGIS.PGPORT}}/${{PostGIS.PGDATABASE}}`
   **[Verificar]** los nombres de esas variables.
4. En **Settings**, **Networking**, se usa **Generate Domain** para obtener la URL
   pública con HTTPS.
5. Se lanza el despliegue con **Deploy**. Railway ejecuta, en este orden:
   1. la construcción de la imagen;
   2. `alembic upgrade head` (pre-deploy); si falla, el despliegue no avanza;
   3. el arranque de la API en el puerto que Railway asigna (`PORT`);
   4. la espera de una respuesta 200 en `/health` (hasta 100 segundos), tras la
      cual cambia a la versión nueva.

## 3. Verificar (cierre de TASK-004)

```powershell
curl https://<dominio>.up.railway.app/health
```

La respuesta esperada es `{"status":"ok"}` con código 200. Una vez obtenida:

- se anotan la URL y la fecha en `tasks.md` (TASK-004) y se marca la tarea `[x]`;
- se adjunta la salida del `curl` como evidencia de TASK-004;
- se actualiza la fila de HTTPS de `docs/controles_seguridad.md`, que pasa a ser
  verificable.

## 4. Cargar los datos iniciales (opcional para TASK-004)

Después del despliegue la base tiene las tablas, pero está vacía. El catálogo de la
zona piloto (4 municipios, departamentos y enfermedades) se carga con un script
existente e idempotente, que se ejecuta desde una máquina del equipo contra la base
de Railway:

1. En el servicio de la base de datos se activa el acceso público: **Settings**,
   **Networking**, **TCP Proxy** (**[Verificar]** el nombre exacto). Se copia la
   URL pública de conexión.
2. Desde el directorio `dengue-malaria-prediccion/`, con el entorno virtual
   activado:

```powershell
$env:DATABASE_URL = "<URL pública de la base>"
$env:SECRET_KEY = "cualquier-valor-local"
python -m app.etl.seed_catalogo
Remove-Item Env:DATABASE_URL, Env:SECRET_KEY
```

3. Al terminar se desactiva el TCP Proxy. Mientras está activo, la base queda
   expuesta a Internet y protegida solo por su contraseña.

Todavía no existe un script que cargue en la base los CSV de casos y clima; solo
existen las funciones de los conectores, que usan los tests. La tabla `roles`
también sigue vacía y la necesitan TASK-017 y TASK-018. Ninguna de las dos
carencias afecta a `/health`.

## 5. Qué ocurre en cada push

Los pasos 1 a 4 se hacen una sola vez. Después, cada commit en la rama conectada
despliega automáticamente: construcción, migraciones, healthcheck y cambio de
versión. Quedan como tareas manuales únicamente:

- cambiar variables de entorno;
- cargar datos nuevos en la base de datos;
- agregar servicios (frontend, job semanal).

Railway ofrece la opción "Wait for CI" para esperar a GitHub Actions, pero el
repositorio no tiene hoy ningún workflow y existen
[reportes de que a veces omite despliegues](https://station.railway.com/questions/wait-for-ci-skips-deployments-despite-su-3829796b).

## 6. Solución de problemas

| Síntoma | Causa probable |
|---|---|
| El despliegue falla en "Pre-deploy" | `DATABASE_URL` mal referenciada o apuntando a la URL pública, o PostGIS no activo (paso 1.4). Se revisan los logs del pre-deploy. |
| La API no arranca por `SECRET_KEY` | La variable falta, es la de ejemplo o tiene menos de 32 caracteres. |
| El healthcheck falla o aparece "service unavailable" | Railway no encontró `railway.toml` (se revisa Config File Path) o la aplicación tarda más de 100 segundos en responder. |
| `could not translate host name ...railway.internal` | La API y la base de datos no están en el mismo proyecto y entorno. |
| Los datos desaparecen al reiniciar la base | La base de datos no tiene volumen. |
| Se necesita volver a la versión anterior | En **Deployments** se elige la versión anterior y **Redeploy**. Esto no deshace las migraciones ya aplicadas. |

## 7. Desventajas conocidas

- No es gratuito de forma sostenida: ofrece un crédito de prueba o el plan Hobby de
  USD 5 mensuales. Los precios vigentes se consultan en railway.com/pricing.
- La base de datos de la plantilla no es un servicio administrado: no hay garantía
  de copias de seguridad ni de actualizaciones, por lo que conviene hacer `pg_dump`
  periódicos.
- Hay una sola instancia, sin alta disponibilidad, de modo que NFR-003 (99 %) no
  queda garantizado.
- Cada push a la rama conectada va directo a producción, porque no existe un
  entorno de pruebas.
- El job semanal y el frontend requieren servicios adicionales y ajustes que no
  están hechos. En particular, el `nginx.conf` del frontend apunta a `api:8000`,
  un nombre válido solo en Docker Compose.
- Existe dependencia del proveedor (ADR-003). Si se cambia, el `Dockerfile` se
  reutiliza, pero la configuración debe rehacerse.

## 8. Verificado en local (2026-10-26)

Con la imagen `api` real, una base de datos nueva y vacía, `DATABASE_URL` con
esquema `postgres://`, `ENVIRONMENT=production` y `PORT=3000`, el comando
`alembic upgrade head` creó las tablas y la API respondió 200 en `/health`. Esto
reproduce el pre-deploy y el arranque, pero no el despliegue en Railway.
