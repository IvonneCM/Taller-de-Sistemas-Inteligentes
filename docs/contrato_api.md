# Contrato: API REST (TASK-019 a TASK-023)

**Publica:** Dilan Mamani (API) · **Lo necesitan:** Tania y Adriana (dashboard y paneles), Ivonne (login/RBAC y motor de predicción)
**Verificado contra:** PostgreSQL 17 + PostGIS 3.6 locales; `pytest tests/api` (2026-10-26)
**Fuente de verdad:** `dengue-malaria-prediccion/app/api/routes/`, `app/schemas/` y `app/services/`. La documentación interactiva sale de FastAPI (`/docs`, `/openapi.json`).
**Relacionado:** `dengue-malaria-prediccion/design.md` §4 · [`contrato_esquema_bd.md`](./contrato_esquema_bd.md)

Estado: **implementados** los 5 endpoints de abajo. `/auth/login` (TASK-017), el resto del RBAC (TASK-018) y los endpoints de priorización, recursos y desempeño (TASK-024/025/026) siguen pendientes.

## Autenticación

Todas las rutas, salvo `/health`, exigen `Authorization: Bearer <JWT de acceso>`. Sin token o con token inválido, vencido o de refresco → **401**. Con token válido pero sin permiso para la ruta → **403**.

### Claims que debe emitir `/auth/login` (Ivonne, TASK-017)

| Claim | Obligatorio | Contenido |
|---|---|---|
| `sub` | sí | id del usuario, como texto de un entero |
| `rol` | sí | `autoridad`, `sedes`, `epidemiologo`, `coordinador_municipal` o `admin` |
| `exp` | sí | expiración (la valida python-jose) |
| `municipio_asignado_id` | no | entero; hoy ningún endpoint lo usa |
| `type` | no | si vale `refresh`, el token se rechaza como token de acceso |

Firma con `SECRET_KEY` y `ALGORITHM` de las variables de entorno (sin valor por defecto para la clave). `app/api/deps.py` expone `get_usuario_actual` y `require_role(*roles)`; TASK-018 puede ampliarlos sin cambiar sus firmas.

## Endpoints

| Método y ruta | Roles | Tarea / REQ |
|---|---|---|
| `GET /zonas/riesgo` | todos | TASK-019 · REQ-001, REQ-006 |
| `GET /zonas/{municipio_id}/prediccion` | todos (el contenido depende del rol) | TASK-020 · REQ-002/003/004/007 |
| `GET /zonas/{municipio_id}/historial` | `epidemiologo`, `admin` | TASK-021 · REQ-008 |
| `GET /alertas` | todos | TASK-022 · REQ-009 |
| `POST /admin/umbrales` | `admin` | TASK-023 · REQ-010 |

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

## Lo que esta API todavía no hace

- No emite tokens ni hay usuarios ni roles cargados (TASK-017/018, Ivonne). Mientras tanto, las pruebas firman sus propios tokens.
- No hay predicciones reales en la base hasta que exista `app/ml/prediccion.py` (TASK-014). Los endpoints devuelven listas vacías o 404 sin ellas.
- No restringe por `municipio_asignado_id` (un coordinador municipal ve todas las zonas); el diseño no lo pide.
- Los roles con vista completa de predicción (`epidemiologo`, `admin`) siguen el criterio de mínimo privilegio; ampliar la lista es cambiar `ROLES_DETALLE_COMPLETO` en `app/api/deps.py`.
