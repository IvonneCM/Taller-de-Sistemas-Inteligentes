# Diseño del Sistema — Predicción Temprana de Brotes de Dengue/Malaria

**Versión:** 1.0
**Fecha:** 2026-08-24
**Basado en:** `requirements.md` v1.0

> ⏸️ **Estado:** diseño de arquitectura vigente (ver también los ADR en
> `../docs/adr/` y los diagramas C4 en `../docs/c4/`), pero la
> implementación del backend está en pausa hasta cerrar la primera
> evaluación. §10 se actualizó el 2026-09-16/17: las preguntas sobre fuente
> climática y epidemiológica ya están resueltas con datos reales; la zona
> piloto sigue sin confirmación oficial del equipo.

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
| Despliegue | Railway (API + PostgreSQL/PostGIS) | Ver justificación acordada con el usuario |
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

### `usuarios` y `roles`
| Tabla | Campos clave |
|---|---|
| usuarios | id, email (UNIQUE), password_hash, rol_id (FK), municipio_asignado_id (NULL si no aplica) |
| roles | id, nombre (ej. "autoridad", "sedes", "epidemiologo", "coordinador_municipal", "admin") |

## 4. Endpoints principales de la API

| Método | Ruta | REQ relacionado | Rol requerido |
|---|---|---|---|
| POST | `/auth/login` | REQ-019 | público |
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
| GET | `/departamentos` | REQ-017 | todos |
| GET | `/enfermedades` | REQ-018 | todos |

Todas las rutas (excepto `/auth/login`) requieren JWT válido; el control de
qué campos se devuelven según el rol se implementa en la capa de servicio,
no en el frontend (para no exponer datos vía API directa) — refuerza
REQ-007, REQ-019 y REQ-020.

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
[`../docs/controles_seguridad.md`](../docs/controles_seguridad.md). En la fase
actual, JWT, RBAC, hashing y HTTPS son controles diseñados pero todavía no
implementados ni verificados en un despliegue.

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
├── requirements.txt
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
  Epidemiológico N.º 13 (2026), acumulados municipales SE1-13 de dengue y
  malaria. Ver `docs/eda_inicial.md` §2.1. **Pendiente:** esta fuente entrega
  acumulados, no series semana-a-semana por municipio; esa granularidad
  sigue sin confirmarse (ver limitación en `docs/eda_inicial.md` §16).
- ¿Cuál será la zona piloto específica (departamento/municipio) para validar
  la precisión espacial del 75% y la anticipación de 2 semanas? **Estado de
  facto, no confirmado oficialmente:** el EDA real solo tiene cruce de
  clima + epidemiología en 4 municipios — Guayaramerín (Beni), Ixiamas, Palos
  Blancos y San Buenaventura (La Paz) — por ser los únicos con estación
  SENAMHI activa en el periodo descargado. El equipo aún no decidió
  formalmente si estos 4 son la zona piloto del proyecto o si se ampliará la
  descarga a otros municipios (ver `docs/cierre_sprint1.md` §3.2).
- ¿Se requiere notificación por correo electrónico para las alertas en esta
  primera versión, o basta con la vista en el dashboard?
- ¿El modelo se re-entrenará periódicamente (ej. mensual) o solo una vez
  para el alcance del proyecto universitario?
