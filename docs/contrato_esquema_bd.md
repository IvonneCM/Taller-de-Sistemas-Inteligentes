# Contrato: esquema de base de datos (TASK-005, TASK-006, TASK-007)

**Publica:** Tania Pérez (capa de datos) · **Lo necesitan:** Ivonne (features/motor de predicción), Dilan (API)
**Verificado contra:** PostgreSQL 16 + PostGIS 3.4, aplicando `alembic upgrade head` (2026-10-25)
**Fuente de verdad:** los modelos en `dengue-malaria-prediccion/app/models/` y la migración `alembic/versions/2a95c198fba5_*.py`. Este documento se genera de la base real; si una columna cambia, se actualiza en el mismo commit.
**Relacionado:** [`contrato_esquema_datos_procesados.md`](./contrato_esquema_datos_procesados.md) (los CSV del pipeline, otro contrato distinto) · `dengue-malaria-prediccion/design.md` §3

## Cómo levantar la base y verificar

```bash
docker run -d --name dengue-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=dengue_malaria \
  -p 127.0.0.1:5433:5432 postgis/postgis:16-3.4      # 5433 si el 5432 está ocupado
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/dengue_malaria
cd dengue-malaria-prediccion
.venv/bin/alembic upgrade head
.venv/bin/python -m app.etl.seed_catalogo            # departamentos, enfermedades, 4 municipios piloto
.venv/bin/python -m pytest tests -q                   # 23 tests
```

Las credenciales son solo para desarrollo local (las mismas de `.env.example`); nunca se suben credenciales reales.

## Tablas que existen hoy

### `departamentos`
| Columna | Tipo | Restricción |
|---|---|---|
| `id` | serial | PK |
| `nombre` | varchar(100) | NOT NULL, UNIQUE |

### `enfermedades`
| Columna | Tipo | Restricción |
|---|---|---|
| `id` | serial | PK |
| `nombre` | varchar(50) | NOT NULL, UNIQUE. Valores sembrados: `dengue`, `malaria` (minúsculas). |

### `municipios`
| Columna | Tipo | Restricción |
|---|---|---|
| `id` | serial | PK |
| `nombre` | varchar(150) | NOT NULL. **No es UNIQUE** (ver advertencias). Se guarda en MAYÚSCULAS sin tildes. |
| `departamento_id` | int | NOT NULL, FK → `departamentos.id` |
| `geometria` | geometry(MultiPolygon, 4326) | NOT NULL. Índice GIST `idx_municipios_geometria`. |
| `poblacion_estimada` | int | NULL permitido (dato referencial, hoy vacío) |

### `casos_epidemiologicos`
| Columna | Tipo | Restricción |
|---|---|---|
| `id` | serial | PK |
| `municipio_id` | int | NOT NULL, FK → `municipios.id` |
| `enfermedad_id` | int | NOT NULL, FK → `enfermedades.id` |
| `fecha_reporte` | date | NOT NULL. **Su significado depende de la granularidad, ver abajo.** |
| `casos_confirmados` | int | NOT NULL, `CHECK >= 0` (`ck_casos_no_negativos`) |
| `fuente` | varchar(100) | NOT NULL. Máximo 100 caracteres (un texto más largo falla en PostgreSQL). |
| `fecha_ingesta` | timestamptz | NOT NULL, default `now()` |
| `es_dato_imputado` | boolean | NOT NULL, default `false` |

Restricción única: `(municipio_id, enfermedad_id, fecha_reporte, fuente)` (`uq_caso_municipio_enfermedad_fecha_fuente`), que hace la ingesta idempotente.

### `datos_climaticos`
| Columna | Tipo | Restricción |
|---|---|---|
| `id` | serial | PK |
| `municipio_id` | int | NOT NULL, FK → `municipios.id` |
| `fecha` | date | NOT NULL (clima **diario**) |
| `temperatura_media_c` | numeric(4,1) | NULL permitido |
| `humedad_relativa_pct` | numeric(4,1) | NULL permitido |
| `precipitacion_mm` | numeric(6,1) | NULL permitido |
| `fuente` | varchar(100) | NOT NULL |
| `fecha_ingesta` | timestamptz | NOT NULL, default `now()` |
| `es_dato_imputado` | boolean | NOT NULL, default `false` |

Restricción única: `(municipio_id, fecha)` (`uq_clima_municipio_fecha`).

### `roles` y `usuarios`
| Tabla | Columnas |
|---|---|
| `roles` | `id` PK, `nombre` varchar(50) NOT NULL UNIQUE |
| `usuarios` | `id` PK, `email` varchar(150) NOT NULL UNIQUE, `password_hash` varchar(255) NOT NULL, `rol_id` NOT NULL FK → `roles.id`, `municipio_asignado_id` NULL FK → `municipios.id` |

Sin ningún campo de datos personales de pacientes (REQ-020). Solo existe el **hash** de la contraseña (bcrypt llega con TASK-017). Un test (`tests/test_modelo_usuarios.py`) falla si alguien agrega una columna de contraseña en texto plano o de datos personales.

## Cómo interpretar `casos_epidemiologicos.fecha_reporte`

| Enfermedad | Qué hay | `fecha_reporte` | `fuente` | Cómo leerla |
|---|---|---|---|---|
| **Dengue** | **Serie semanal** por municipio (SE1-13 de 2026) | **Domingo** de la semana ISO | `Min. Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13 (serie semanal)` | `casos_confirmados` = casos de **esa semana** |
| **Malaria** | Solo **acumulado** SE1-13 por municipio | Domingo de la SE13 (cierre del periodo) | `Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13` | `casos_confirmados` = acumulado SE1-13, **no** un conteo semanal |

Reglas para quien consuma la tabla (features, API):
- **Nunca sumar filas acumuladas y semanales de la misma enfermedad:** duplicaría los casos. Filtrar por `fuente`.
- Para construir rezagos (TASK-011) usar solo dengue semanal. Malaria no admite rezagos semanales con estos datos.
- `es_dato_imputado = false` en todo lo cargado hoy: son conteos reales del boletín, nada estimado.
- La zona piloto cargada son **4 municipios**: Guayaramerín, Ixiamas, Palos Blancos y San Buenaventura. Para dengue eso son 52 filas semanales (4 × 13).

## Advertencias conocidas (no son errores, son límites actuales)

1. **`municipios.geometria` es referencial.** Cada municipio piloto es un cuadrado de ~5 km centrado en la estación SENAMHI; no hay límites oficiales del INE. No usar para calcular áreas ni distancias entre límites.
2. **`municipios.nombre` no es único**, y los conectores buscan por nombre. Con el catálogo piloto no hay colisiones; al ampliarlo (hay otros "San Pedro", etc.) hay que desambiguar por departamento.
3. **`roles` está vacío.** El seed (`app/etl/seed_catalogo.py`) no carga los roles previstos en `design.md` (`autoridad`, `sedes`, `epidemiologo`, `coordinador_municipal`, `admin`). **Pendiente para Ivonne** (TASK-017/018) o para una tarea de seed.
4. **Datos provisionales.** El boletín se corrige después: la última semana publicada muestra ~39 % de los casos que terminan reportándose (ver `data/processed/dengue_revisiones_resumen.csv`).
5. **Un año, 13 semanas.** No hay historia de años anteriores en la base.

## Tablas previstas en `design.md` §3 que todavía NO existen

`modelos`, `predicciones`, `alertas`, `umbrales_configuracion`, `brotes_confirmados`. Las crean las tareas del motor de predicción y de alertas (Ola 1/2 de Ivonne y Dilan). Cuando se agreguen, este contrato se amplía en el mismo commit que la migración.
