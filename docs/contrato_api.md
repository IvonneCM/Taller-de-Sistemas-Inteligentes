# Contrato: API REST (TASK-019 a TASK-023)

**Publica:** Dilan Mamani (API) · **Lo necesitan:** Tania y Adriana (dashboard y paneles), Ivonne (login/RBAC y motor de predicción)
**Verificado contra:** PostgreSQL 17 + PostGIS 3.6 locales; `pytest` y `scripts/smoke_test.py` (2026-10-26)
**Fuente de verdad:** `dengue-malaria-prediccion/app/api/routes/`, `app/schemas/` y `app/services/`. La documentación interactiva sale de FastAPI (`/docs`, `/openapi.json`).
**Relacionado:** `dengue-malaria-prediccion/design.md` §4 · [`contrato_esquema_bd.md`](./contrato_esquema_bd.md)

Estado: **implementados** los endpoints de abajo, el login con JWT y el control de acceso por rol. Siguen pendientes los de priorización, recursos y desempeño (TASK-024, 025 y 026).

## Autenticación

Todas las rutas, salvo `/health`, `/health/ready` y `/auth/*`, exigen `Authorization: Bearer <access token>`. Sin token, o con uno inválido, vencido o de refresco → **401**. Con token válido pero sin permiso → **403**.

| Ruta | Qué hace |
|---|---|
| `POST /auth/login` | Formulario `username` (correo) y `password`. Devuelve `access_token`, `refresh_token`, `token_type` y `expires_in` (segundos) |
| `POST /auth/refresh` | Cuerpo JSON `{"refresh_token": "..."}`. Entrega un par nuevo y **revoca** el refresh usado |
| `POST /auth/logout` | Cuerpo JSON `{"refresh_token": "..."}`. Revoca el token; responde 204 aunque ya no fuera válido |

El rol sale de la base de datos en cada petición (`app/api/deps.py`: `get_current_user` y `require_role`), no del token: un cambio de rol rige de inmediato. Implementado por TASK-017 y 018.

**Cliente web:** el access token se guarda solo en memoria y el refresh token en `sessionStorage` para sobrevivir a una recarga (compromiso aceptado para el MVP, riesgo M-11 en `risk_register.md`). Ante un 401 se refresca una vez y se reintenta; si el refresco falla, se pide entrar de nuevo.

## Endpoints

| Método y ruta | Roles | Tarea / REQ |
|---|---|---|
| `GET /zonas/riesgo` | todos | TASK-019 · REQ-001, REQ-006 |
| `GET /zonas/{municipio_id}/prediccion` | todos (el contenido depende del rol) | TASK-020 · REQ-002/003/004/007 |
| `GET /zonas/{municipio_id}/historial` | `epidemiologo`, `admin` | TASK-021 · REQ-008 |
| `GET /alertas` | todos | TASK-022 · REQ-009 |
| `POST /admin/umbrales` | `admin` | TASK-023 · REQ-010 |
| `GET /casos/resumen` | todos | TASK-047 · REQ-008, REQ-014 |
| `GET /health` · `GET /health/ready` | público | TASK-040 · NFR-003 |

`{municipio_id}` es el id del municipio (la zona base). Errores: 404 si la zona, enfermedad o departamento no existe; 422 si un parámetro es inválido (fecha mal escrita, `desde` posterior a `hasta`, número fuera de rango).

### `GET /zonas/riesgo`

Query opcional: `enfermedad_id`. Devuelve una fila por **zona y enfermedad** con su predicción vigente (la última generada), con el riesgo más alto primero y luego la mayor probabilidad. Una zona sin predicciones no aparece.

```json
{
  "municipio_id": 1, "municipio": "GUAYARAMERIN",
  "departamento_id": 1, "departamento": "Beni",
  "enfermedad_id": 1, "enfermedad": "dengue",
  "nivel_riesgo": "alto", "probabilidad_pct": 82.5, "nivel_confianza": "medio",
  "fecha_generacion": "2026-03-02T12:00:00Z", "fecha_estimada_riesgo": "2026-03-27",
  "centroide": {"lat": -10.83391, "lon": -65.34004},
  "geometria": {"type": "MultiPolygon", "coordinates": ["..."]}
}
```

`geometria` es GeoJSON EPSG:4326. En la zona piloto es un **cuadrado referencial** de ~5 km, no el límite oficial del INE. Para agrupar por departamento (selector de TASK-027), usar `departamento_id`.

### `GET /zonas/{municipio_id}/prediccion`

Query opcional: `enfermedad_id`. 404 si la zona aún no tiene predicciones. El campo `vista` indica qué recibió el usuario:

| `vista` | Roles | Campos por predicción |
|---|---|---|
| `completa` | `epidemiologo`, `admin` | `enfermedad_id`, `enfermedad`, `nivel_riesgo`, `probabilidad_pct`, `nivel_confianza`, `fecha_generacion`, `fecha_estimada_riesgo` **más** `prediccion_id`, `modelo_id`, `modelo_nombre`, `modelo_version` y `variables_explicativas` (`[{variable, peso}]`, ordenadas por influencia) |
| `resumida` | `autoridad`, `sedes`, `coordinador_municipal` | solo los 7 primeros campos |

El servidor no envía los campos técnicos a la vista resumida (ni siquiera en `null`). La probabilidad y la confianza van en ambas vistas porque REQ-003 las exige en toda predicción visible.

### `GET /zonas/{municipio_id}/historial`

Query opcional: `enfermedad_id`, `desde`, `hasta` (`YYYY-MM-DD`). Devuelve `predicciones` (en orden cronológico) y `brotes_confirmados`, más `ventana_correlacion_dias` (7).

Cada predicción trae `brote_confirmado` (bool), `brote_confirmado_id`, `fecha_brote_confirmado` y `anticipacion_dias` (días entre generar la predicción y confirmarse el brote). **Regla de correlación (referencial):** hay "brote confirmado" si existe uno de la misma enfermedad y zona a no más de 7 días de `fecha_estimada_riesgo`; si hay varios se toma el más cercano. Es una comparación descriptiva, no una métrica validada de precisión (NFR-001/002). `desde`/`hasta` filtran las predicciones por fecha de generación (UTC) y los brotes por fecha de confirmación; la correlación usa todos los brotes de la zona, así que un brote fuera del rango puede aparecer referenciado en una predicción sin estar en la lista.

### `GET /alertas`

Query opcional: `municipio_id`, `enfermedad_id`, `desde`, `hasta` (sobre la fecha de emisión, UTC), `limite` (1-500, por defecto 100) y `desplazamiento`. Las más recientes primero. Cada alerta trae `justificacion` y `variables_explicativas` (REQ-005); una alerta cuya predicción no tenga variables no se publica. No existe un campo "activa": el panel decide qué es reciente con `fecha_emision`.

### `POST /admin/umbrales`

```json
{"enfermedad_id": 1, "departamento_id": null, "umbral_probabilidad_pct": 65.5}
```

`departamento_id: null` fija el umbral general de la enfermedad. Crea (**201**) o actualiza (**200**) el umbral de ese par, sin duplicar. El valor debe estar entre 0 y 100 y no se aceptan campos extra. El motor de alertas (TASK-015) debe leerlo con `app.services.umbrales.obtener_umbral(db, enfermedad_id, departamento_id)`: prioridad al umbral del departamento, luego el general, luego **70 %** (valor referencial tomado del ejemplo de REQ-009). Se consulta la BD en cada llamada, sin caché, así que un cambio rige desde la siguiente evaluación.

### `GET /casos/resumen`

Query opcional: `enfermedad_id`. Casos **observados** (no predichos) por municipio y enfermedad, con `geometria` y `centroide` para el mapa. Una fila por municipio y enfermedad:

| Campo | Significado |
|---|---|
| `granularidad` | `semanal` (una fila por semana; dengue) o `acumulado` (un total del periodo; malaria, ver ADR-005) |
| `total_casos`, `desde`, `hasta`, `registros` | Suma, rango de fechas y número de filas de la fuente |
| `fuente` | Boletín de origen |

Si hay serie semanal se usa solo esa; **nunca se suman filas semanales con acumuladas** de la misma enfermedad. Son conteos agregados: sin datos de pacientes.

### `GET /health` y `GET /health/ready`

`/health` responde `{"status":"ok"}` si la API vive y no consulta nada. `/health/ready` además ejecuta `SELECT 1`: 200 `{"status":"ok","database":"ok"}` o **503** `{"status":"degraded","database":"unavailable"}` con `Retry-After: 5`. Es lo que usa `scripts/smoke_test.py`.

## Errores y diagnóstico (TASK-040)

| Código | Cuándo | Cuerpo |
|---|---|---|
| 401 / 403 | Sin sesión / sin permiso | `{"detail": "..."}` |
| 404 | La zona, enfermedad o departamento no existe | `{"detail": "..."}` |
| 422 | Entrada inválida | `{"detail": [{"loc","msg","type"}], "request_id"}`; **no** incluye el valor enviado (podría ser una contraseña) |
| 503 | Base de datos caída o consulta que excede el tiempo | `{"detail": "El servicio de datos no esta disponible...", "request_id"}` y `Retry-After: 5` |
| 500 | Error no previsto | `{"detail": "Error interno del servidor.", "request_id"}`; la traza queda solo en el log del servidor |

Cada respuesta lleva `X-Request-ID` (se acepta el del cliente si es `[A-Za-z0-9._-]{1,64}`; si no, se genera uno) y ese identificador aparece en todos los logs de la petición. Los logs registran método, ruta, estado y duración; **nunca** cabeceras, cuerpos ni cadenas de consulta. Tiempos: conexión 5 s, consulta 15 s y espera de conexión del pool 10 s (configurables).

## Lo que esta API todavía no hace

- No genera alertas: las crea el job `app/ml/evaluacion_alertas.py` (TASK-015) con el umbral vigente (`obtener_umbral`); la API solo las lista. Con el umbral por defecto (70 %) las predicciones actuales no alertan: un admin lo cambia con `POST /admin/umbrales` y se ejecuta `python -m app.ml.evaluacion_alertas`.
- No hay predicciones de malaria (no existe modelo; ADR-005) ni se cargan brotes confirmados (no hay fuente), así que el historial no muestra brotes.
- No expone la ingesta (`POST /datos/...` de `design.md` §4): los datos entran por comando (`python -m app.etl.seed_demo`).
- No restringe por `municipio_asignado_id`: un coordinador municipal ve todas las zonas; el diseño no lo pide.
- Los roles con vista completa de predicción (`epidemiologo`, `admin`) siguen el criterio de mínimo privilegio; ampliar la lista es cambiar `ROLES_DETALLE_COMPLETO` en `app/api/roles.py`.
