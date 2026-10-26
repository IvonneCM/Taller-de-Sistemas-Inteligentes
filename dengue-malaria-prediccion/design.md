# Diseño del Sistema — Predicción Temprana de Brotes de Dengue/Malaria

**Versión:** 1.0
**Fecha:** 2026-08-24
**Basado en:** `requirements.md` v1.0

> ▶️ **Estado (2026-10-25):** diseño vigente. La capa de datos (§3, TASK-005 a
> TASK-010) está implementada y verificada contra PostgreSQL 16 + PostGIS 3.4;
> las divergencias entre este documento y la base real están anotadas en §3.
> §10 se actualizó el 2026-10-25: la granularidad epidemiológica y la zona
> piloto quedaron resueltas por el reparto "Listo para Empezar".

---

## 1. Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend / API | Python 3.12 + FastAPI | Tipado, generación automática de OpenAPI, buen ecosistema para ML |
| Base de datos | PostgreSQL 16 + extensión **PostGIS** | Necesaria para consultas geoespaciales (zonas, municipios, mapas de calor) |
| Modelado ML | scikit-learn / XGBoost (baseline) + SHAP (explicabilidad) | Balance entre desempeño y explicabilidad, adecuado para series temporales tabulares con pocos datos |
| Orquestación de tareas | APScheduler o Celery + Redis (según carga) | Ejecutar el pipeline de predicción semanalmente |
| Frontend / Dashboard | React + librería de mapas (ej. Leaflet o Mapbox GL) | Mapas de calor interactivos y vistas por rol |
| Autenticación | JWT (OAuth2 password flow de FastAPI) | Estándar, simple de integrar con RBAC |
| Despliegue | Railway (API + PostgreSQL/PostGIS) — **pendiente de confirmar** | Ver justificación acordada con el usuario. El despliegue (TASK-004) está en espera y el proveedor puede cambiar; ver §10 |
| Contenedores | Docker: tres imágenes — `api` (323 MB), `ml` (2,3 GB, ETL y predicción semanal) y `web` (74 MB, nginx); Python 3.12 fijado | La API solo lee resultados, así que no carga pandas/xgboost/shap; el job de predicción corre fuera de FastAPI con la imagen `ml`. La BD local usa `postgis/postgis:16-3.4` |
| Entrenamiento de modelo (offline) | Google Colab o servidor de la universidad | Evita cargar cómputo pesado en el entorno de producción liviano |

> Nota: los nombres de librerías específicas (ej. XGBoost vs. Prophet vs.
> LSTM) son una propuesta de partida razonable para un proyecto
> universitario; deben validarse con los datos reales disponibles antes de
> considerarse definitivos. Ver sección 8 (Preguntas abiertas).

## 2. Vista general de la arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                          │
│  Datos epidemiológicos (SNIS/SEDES) │ Datos climáticos públicos  │
│  (ej. SENAMHI, satelitales)         │ Datos geográficos (INE)    │
└───────────────┬─────────────────────────────┬────────────────────┘
                │                              │
                ▼                              ▼
        ┌───────────────────────────────────────────┐
        │        CAPA DE INGESTA (ETL)               │
        │  Conectores por fuente → validación →      │
        │  limpieza → imputación → normalización     │
        └───────────────────┬─────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────┐
        │      BASE DE DATOS (PostgreSQL + PostGIS)  │
        │  Tablas de zonas, casos, clima, modelos,   │
        │  predicciones, alertas, usuarios           │
        └───────────────────┬─────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────┐
        │     MOTOR DE PREDICCIÓN (batch semanal)    │
        │  Feature engineering → modelo → SHAP →     │
        │  persistencia de predicción y explicación  │
        └───────────────────┬─────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────┐
        │            API REST (FastAPI)              │
        │  Auth/RBAC · Predicciones · Alertas ·      │
        │  Mapas de calor · Métricas de desempeño    │
        └───────────────────┬─────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────┐
        │      DASHBOARD WEB (React + mapas)         │
        │  Vista autoridad · Vista técnica/           │
        │  epidemiólogo · Vista municipal             │
        └───────────────────────────────────────────┘
```

## 3. Modelo de datos (PostgreSQL + PostGIS)

### `departamentos`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| nombre | VARCHAR(100) | UNIQUE, NOT NULL |

### `municipios` (zona geográfica base)
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| nombre | VARCHAR(150) | NOT NULL |
| departamento_id | INTEGER | FK → departamentos.id, NOT NULL |
| geometria | GEOMETRY(MULTIPOLYGON, 4326) | PostGIS, NOT NULL — soporta REQ-006 |
| poblacion_estimada | INTEGER | NULL permitido (dato referencial) |

### `enfermedades`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| nombre | VARCHAR(50) | UNIQUE, NOT NULL (ej. "dengue", "malaria") — soporta REQ-018 |

### `casos_epidemiologicos`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| municipio_id | INTEGER | FK → municipios.id, NOT NULL |
| enfermedad_id | INTEGER | FK → enfermedades.id, NOT NULL |
| fecha_reporte | DATE | NOT NULL |
| casos_confirmados | INTEGER | NOT NULL, CHECK >= 0 |
| fuente | VARCHAR(100) | NOT NULL — soporta REQ-015 |
| fecha_ingesta | TIMESTAMP | NOT NULL DEFAULT now() |
| es_dato_imputado | BOOLEAN | DEFAULT false — soporta REQ-013 |

**Divergencias verificadas contra la base real (2026-10-25):**
- `fecha_ingesta` es `TIMESTAMPTZ` (con zona horaria), no `TIMESTAMP`.
- `es_dato_imputado` es `NOT NULL DEFAULT false` (el diseño decía solo DEFAULT).
- Se agregó `UNIQUE (municipio_id, enfermedad_id, fecha_reporte, fuente)`
  (`uq_caso_municipio_enfermedad_fecha_fuente`) para que la ingesta sea
  idempotente.
- **Semántica de `fecha_reporte`:** domingo de la semana ISO en filas
  SEMANALES (dengue: serie real por municipio) y cierre del periodo en filas
  ACUMULADAS (malaria: solo existen acumulados SE1-k). Las filas semanales y
  acumuladas de una misma enfermedad no deben mezclarse (duplicarían casos);
  se distinguen por `fuente`.
- `municipios.nombre` no es UNIQUE: los conectores buscan por nombre con
  `.first()`, lo que es ambiguo si dos departamentos tienen un municipio del
  mismo nombre (p. ej. San Pedro). Hoy el catálogo piloto no tiene colisiones.

### `datos_climaticos`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| municipio_id | INTEGER | FK → municipios.id, NOT NULL |
| fecha | DATE | NOT NULL |
| temperatura_media_c | NUMERIC(4,1) | NULL permitido |
| humedad_relativa_pct | NUMERIC(4,1) | NULL permitido |
| precipitacion_mm | NUMERIC(6,1) | NULL permitido |
| fuente | VARCHAR(100) | NOT NULL |
| fecha_ingesta | TIMESTAMP | NOT NULL DEFAULT now() |
| es_dato_imputado | BOOLEAN | DEFAULT false |

*Restricción compuesta:* `UNIQUE(municipio_id, fecha)` para evitar duplicados.

### `modelos`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| nombre | VARCHAR(100) | NOT NULL |
| version | VARCHAR(20) | NOT NULL |
| enfermedad_id | INTEGER | FK → enfermedades.id |
| fecha_entrenamiento | TIMESTAMP | NOT NULL |
| metricas_entrenamiento | JSONB | ej. {"precision_espacial": 0.78} |

### `predicciones`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| municipio_id | INTEGER | FK → municipios.id, NOT NULL |
| enfermedad_id | INTEGER | FK → enfermedades.id, NOT NULL |
| modelo_id | INTEGER | FK → modelos.id, NOT NULL |
| fecha_generacion | TIMESTAMP | NOT NULL DEFAULT now() — soporta REQ-002 |
| fecha_estimada_riesgo | DATE | NOT NULL, CHECK entre 21 y 28 días de fecha_generacion |
| nivel_riesgo | VARCHAR(10) | CHECK IN ('bajo','medio','alto') — soporta REQ-001 |
| probabilidad_pct | NUMERIC(5,2) | CHECK 0-100 — soporta REQ-003 |
| nivel_confianza | VARCHAR(10) | CHECK IN ('bajo','medio','alto') |
| variables_explicativas | JSONB | lista ordenada {variable, peso} — soporta REQ-004 |

*Tabla inmutable a nivel de aplicación (solo INSERT, sin UPDATE) — soporta NFR-009.*

### `alertas`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| prediccion_id | INTEGER | FK → predicciones.id, NOT NULL |
| umbral_aplicado | NUMERIC(5,2) | NOT NULL |
| fecha_emision | TIMESTAMP | NOT NULL DEFAULT now() |
| justificacion | TEXT | NOT NULL — soporta REQ-005 (no nulo: sin justificación no se crea la fila) |

### `umbrales_configuracion`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| enfermedad_id | INTEGER | FK → enfermedades.id |
| departamento_id | INTEGER | FK → departamentos.id, NULL = aplica a todos |
| umbral_probabilidad_pct | NUMERIC(5,2) | NOT NULL — soporta REQ-010 |

### `brotes_confirmados`
| Campo | Tipo | Restricción |
|---|---|---|
| id | SERIAL PK | |
| municipio_id | INTEGER | FK → municipios.id |
| enfermedad_id | INTEGER | FK → enfermedades.id |
| fecha_confirmacion | DATE | NOT NULL — soporta REQ-008 y NFR-002 |
| fuente | VARCHAR(100) | NOT NULL |

**Divergencias de las tablas `predicciones`, `alertas`, `umbrales_configuracion` y `brotes_confirmados` (implementadas en TASK-019 a 023, 2026-10-26):**
- `predicciones.fecha_generacion` y `alertas.fecha_emision` son `TIMESTAMPTZ`, igual que `fecha_ingesta`. El `CHECK` de 21 a 28 días usa la fecha en UTC (`fecha_generacion AT TIME ZONE 'UTC'`) para no depender de la zona horaria de la sesión.
- `predicciones.variables_explicativas` es NOT NULL y un `CHECK` exige que sea una lista JSON; `None` se guarda como NULL de SQL (no como JSON `null`) para que falle el NOT NULL. Una lista vacía se admite en la BD; la regla "sin variables no hay alerta" la aplica TASK-015 y `GET /alertas` filtra las filas incompletas.
- `alertas.justificacion` no puede ser vacía ni de solo espacios; `umbral_aplicado` 0-100.
- `umbrales_configuracion.enfermedad_id` es NOT NULL; hay `UNIQUE (enfermedad_id, departamento_id)` con `NULLS NOT DISTINCT` (PostgreSQL 15 o superior) y `CHECK` 0-100.
- `brotes_confirmados.municipio_id` y `enfermedad_id` son NOT NULL.
- Índice `ix_predicciones_municipio_enfermedad_fecha` para la consulta de "predicción vigente por zona".

### `usuarios` y `roles`
| Tabla | Campos clave |
|---|---|
| usuarios | id, email (UNIQUE), password_hash, rol_id (FK), municipio_asignado_id (NULL si no aplica) |
| roles | id, nombre (ej. "autoridad", "sedes", "epidemiologo", "coordinador_municipal", "admin") |

## 4. Endpoints principales de la API

| Método | Ruta | REQ relacionado | Rol requerido |
|---|---|---|---|
| POST | `/auth/login` | REQ-019 | público |
| POST | `/auth/refresh` | REQ-019, SEG-01 | refresh token válido y no revocado |
| POST | `/auth/logout` | REQ-019, SEG-01 | refresh token válido |
| GET | `/zonas/riesgo` | REQ-001, REQ-006 | todos los roles autenticados |
| GET | `/zonas/{id}/prediccion` | REQ-002, REQ-003, REQ-004 | todos (detalle limitado según rol, REQ-007) |
| GET | `/zonas/{id}/historial` | REQ-008 | epidemiólogo, admin |
| GET | `/alertas` | REQ-009 | todos los roles autenticados |
| POST | `/admin/umbrales` | REQ-010 | admin |
| GET | `/campanas/priorizacion` | REQ-011 | sedes, coordinador_municipal |
| GET | `/municipios/{id}/recursos` | REQ-012 | coordinador_municipal, admin |
| POST | `/datos/clima` (ingesta) | REQ-013, REQ-014, REQ-015 | admin / proceso ETL |
| POST | `/datos/casos` (ingesta) | REQ-013, REQ-014, REQ-015 | admin / proceso ETL |
| GET | `/modelo/desempeno` | REQ-016 | epidemiólogo, admin |
| GET | `/casos/resumen` | REQ-008, REQ-014 | todos los roles autenticados (casos observados por zona; TASK-047) |
| GET | `/health` · `/health/ready` | NFR-003 | público (disponibilidad y base de datos; TASK-040) |
| GET | `/departamentos` | REQ-017 | todos |
| GET | `/enfermedades` | REQ-018 | todos |

**Implementación (TASK-019 a 023):** detalle de parámetros, respuestas y la regla de correlación del historial en [`../docs/contrato_api.md`](../docs/contrato_api.md). Decisiones que este diseño no fijaba:
- `{id}` de `/zonas/{id}/...` es el id del municipio.
- Vista completa de `/zonas/{id}/prediccion` (variables explicativas y modelo): `epidemiologo` y `admin`; el resto recibe la resumida, que mantiene probabilidad y confianza por REQ-003. El filtrado ocurre en el servidor.
- Umbral de alerta por defecto: 70 % (referencial, ejemplo de REQ-009) cuando el admin no configuró ninguno; `POST /admin/umbrales` crea (201) o actualiza (200).
- La autenticación y el RBAC son los de TASK-017/018 (`app/api/deps.py`: `get_current_user`, `require_role`); los endpoints de zonas, alertas y umbrales los reutilizan sin cambios.

Todas las rutas (excepto `/auth/login` y `/auth/refresh`, que validan
credenciales o un refresh token) requieren JWT válido; el control de qué
campos se devuelven según el rol se implementa en la capa de servicio, no
en el frontend (para no exponer datos vía API directa) — refuerza REQ-007,
REQ-019 y REQ-020. `/auth/logout` revoca el refresh token recibido; no
requiere un access token adicional porque el propio refresh token es la
credencial a invalidar.

## 5. Pipeline de predicción (motor ML)

1. **Extracción**: lectura de `casos_epidemiologicos` y `datos_climaticos`
   por municipio, ventana móvil de N semanas.
2. **Limpieza/imputación** (REQ-013): los valores faltantes climáticos se
   tratan mediante una jerarquía reproducible y se marca
   `es_dato_imputado = true`. Con más de 5% y hasta 20% de faltantes la
   predicción continúa con confianza baja; por encima de 20% no se publica
   una predicción operativa. Los reportes epidemiológicos ausentes no se
   convierten en cero ni se imputan silenciosamente. Las reglas completas,
   incluidos retrasos de reporte y criterios de prueba, están en
   [`../docs/reglas_calidad_datos.md`](../docs/reglas_calidad_datos.md).
3. **Feature engineering**: variables rezagadas (lag) de temperatura,
   humedad y precipitación (2-4 semanas atrás), promedio móvil de casos,
   estacionalidad.
4. **Predicción**: modelo clasifica el nivel de riesgo y calcula probabilidad.
5. **Explicabilidad** (REQ-004): cálculo de importancia de variables (SHAP)
   por predicción individual.
6. **Persistencia**: se inserta una fila en `predicciones` (nunca se
   actualiza una predicción existente, ver NFR-009).
7. **Evaluación de alertas** (REQ-009, REQ-005): si `probabilidad_pct` supera
   el umbral configurado y existen variables explicativas, se crea una fila
   en `alertas`.

Este pipeline se ejecuta de forma **batch semanal** (no en tiempo real), lo
cual es coherente con el horizonte de predicción de 3-4 semanas y reduce la
complejidad de infraestructura para un proyecto universitario.

## 6. Seguridad

La matriz completa, el estado de implementación y los criterios de evidencia
se documentan en
[`../docs/controles_seguridad.md`](../docs/controles_seguridad.md). JWT,
RBAC y hashing ya están implementados y probados localmente; HTTPS sigue
pendiente de verificación en un despliegue real.

- Autenticación JWT (OAuth2 password flow), expiración corta de access token
  + refresh token.
- RBAC aplicado en la capa de servicio de FastAPI (dependencias de rol).
- Contraseñas con `bcrypt`.
- HTTPS obligatorio en despliegue (Railway lo provee por defecto en su
  dominio).
- Variables sensibles (credenciales de BD, claves de API climáticas) en
  variables de entorno, nunca en el repositorio.
- No se almacenan datos personales de pacientes (REQ-020): todo dato
  epidemiológico es agregado por municipio y fecha.

## 7. Explicabilidad del modelo

- Se usará **SHAP** (SHapley Additive exPlanations) sobre el modelo elegido
  (compatible con XGBoost/árboles) para producir, por cada predicción, un
  ranking de variables con su contribución.
- El resultado se serializa como JSONB en `predicciones.variables_explicativas`,
  ej.: `[{"variable": "temperatura_media_c", "peso": 0.34}, {"variable": "casos_4_semanas_atras", "peso": 0.28}]`.
- Esto evita el problema de "caja negra" y da soporte directo a REQ-004 y
  REQ-005 (no alertar sin justificación).

## 8. Escalabilidad y extensibilidad

- Nuevas fuentes de datos (REQ-014): se agregan como nuevos módulos
  "conector" en la capa de ingesta que escriben al mismo esquema; no se
  modifica el modelo de datos central.
- Nuevos departamentos (REQ-017): solo requiere cargar geometría en
  `municipios` y datos históricos asociados.
- Nuevas enfermedades (REQ-018): la tabla `enfermedades` ya desacopla la
  lógica de predicción de una enfermedad específica; se requeriría entrenar
  un modelo adicional referenciado en `modelos.enfermedad_id`.
- Separación de entrenamiento (offline, Colab/servidor universidad) y
  servicio de inferencia (API en Railway) permite escalar cómputo de
  entrenamiento sin afectar el servicio en producción.

## 9. Estructura de archivos (backend)

```
dengue-malaria-prediccion/
├── app/
│   ├── main.py                  # instancia FastAPI
│   ├── core/
│   │   ├── config.py             # variables de entorno
│   │   └── security.py           # JWT, hashing
│   ├── models/                   # modelos ORM (SQLAlchemy)
│   │   ├── municipio.py
│   │   ├── caso_epidemiologico.py
│   │   ├── dato_climatico.py
│   │   ├── prediccion.py
│   │   ├── alerta.py
│   │   └── usuario.py
│   ├── schemas/                  # esquemas Pydantic (request/response)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── zonas.py
│   │   │   ├── alertas.py
│   │   │   ├── campanas.py
│   │   │   └── admin.py
│   │   └── deps.py               # dependencias de auth/RBAC
│   ├── etl/
│   │   ├── conectores/           # un módulo por fuente de datos
│   │   └── limpieza.py
│   └── ml/
│       ├── features.py
│       ├── entrenamiento.py      # se corre offline
│       ├── prediccion.py         # se corre en el batch semanal
│       └── explicabilidad.py
├── tests/
├── alembic/                      # migraciones de base de datos
├── Dockerfile                    # targets: api (ligera) y ml (pandas, xgboost, shap); Python 3.12
├── docker-compose.yml            # db PostGIS + api + web (+ ml, profile "jobs")
├── frontend/                     # React + Vite + Leaflet; Dockerfile propio (nginx)
├── requirements.txt              # entorno local completo (incluye los tres de abajo)
├── requirements-api.txt          # imagen api
├── requirements-ml.txt           # imagen ml (xgboost, pandas, shap)
├── requirements-dev.txt          # pytest, black, ruff (solo local)
├── requirements.md
├── design.md
├── tasks.md
└── CONTEXT.md
```

## 10. Preguntas abiertas

- ~~¿Qué fuente exacta de datos climáticos públicos se usará?~~ **Resuelto:**
  SENAMHI Bolivia (WIS 2.0), vía `scripts/descargar_senamhi.py`. Ver
  `docs/eda_inicial.md` §2.2.
- ~~¿Qué fuente de datos epidemiológicos históricos está disponible?~~
  **Resuelto:** Ministerio de Salud y Deportes de Bolivia, Boletín
  Epidemiológico (2026). **Granularidad (resuelta 2026-10-25, decisión 2 del
  reparto):** se adopta serie municipio-semana. Para **dengue** existe: el
  Boletín N.º 13 trae casos por semana y municipio (SE1-13), extraídos y
  verificados en `scripts/extraer_dengue_semanal.py`. Para **malaria** no
  existe en ninguna fuente disponible: solo acumulados SE1-k por boletín;
  restando boletines consecutivos se reconstruyen bloques de varias semanas
  (`data/processed/malaria_municipal_bloques.csv`), nunca semanas inventadas.
  **Decisión (2026-10-25, ADR-005):** en la base de datos malaria se guarda como
  acumulado SE1-13; el modelo de malaria entrena con el panel de bloques en CSV.
  Los datos recientes se corrigen en boletines posteriores (la última semana
  de un boletín muestra ~39 % de sus casos finales); ver
  `data/processed/dengue_revisiones_resumen.csv`.
- ~~¿Cuál será la zona piloto específica?~~ **Resuelto (decisión 1 del
  reparto, 2026-10-25):** los 4 municipios con cruce real de estación SENAMHI
  y epidemiología — Guayaramerín (Beni), Ixiamas, Palos Blancos y San
  Buenaventura (La Paz). **Aclaración:** el catálogo de la base de datos
  carga solo esos 4. El panel de modelado (`panel_semanal_dengue_clima.csv`)
  cubre 28 municipios con clima de reanálisis NASA POWER porque 4 son muy
  pocos para entrenar; ampliar el catálogo de la BD requiere polígonos
  municipales oficiales (hoy son cuadrados referenciales de ~5 km).
- **Proveedor de despliegue (abierta, 2026-10-25):** Railway no es gratuito de
  forma sostenida (crédito de prueba de $5 o plan Hobby de $5/mes). Alternativas
  gratuitas con PostGIS: API en Render o Northflank y base en Neon. Si la API
  corre en un servicio que se duerme sin tráfico, el job semanal (TASK-016)
  debe dispararse desde un cron externo. Decisión del equipo pendiente.
- ¿Se requiere notificación por correo electrónico para las alertas en esta
  primera versión, o basta con la vista en el dashboard?
- ¿El modelo se re-entrenará periódicamente (ej. mensual) o solo una vez
  para el alcance del proyecto universitario?
