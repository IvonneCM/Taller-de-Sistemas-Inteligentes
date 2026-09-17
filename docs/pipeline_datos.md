# Pipeline reproducible de datos (Línea Base — Paso 2)

**Responsable:** Tania Perez
**Sección del backlog:** Build/QA/Deploy
**Implementa:** [`reglas_calidad_datos.md`](./reglas_calidad_datos.md) (autor: Dilan Mamani)
**Se apoya en:** [`eda_inicial.md`](./eda_inicial.md) y los scripts de ingesta/EDA de Adriana Rocha (`scripts/descargar_senamhi.py`, `scripts/procesar_clima.py`, `scripts/integrar_datos.py`)

---

## 1. Qué problema resuelve este pipeline

El EDA de Adriana (`docs/eda_inicial.md`) ya deja documentado un límite
explícito: el control de calidad climático (`scripts/procesar_clima.py`)
identifica valores sospechosos y huecos de cobertura, pero **no imputa
nada** — solo excluye y marca. Por su parte, `docs/reglas_calidad_datos.md`
(Dilan) define el contrato completo de limpieza/imputación pero aclara que
es "una propuesta, no una funcionalidad ya implementada".

Este pipeline (`scripts/limpieza_datos.py`) es esa funcionalidad: toma los
datos ya validados por Adriana y por las fuentes oficiales, y aplica sobre
ellos el contrato de calidad de Dilan de forma ejecutable y reproducible.

**No reemplaza ni reprocesa el trabajo ya hecho.** No vuelve a descargar de
SENAMHI ni a recalcular el control de calidad climático original
(`control_calidad_clima.csv` se sigue generando con `procesar_clima.py`).
Este script arranca desde `data/processed/clima_diario.csv` y desde los
CSV crudos de epidemiología.

## 2. Qué hace, en orden

```text
data/processed/clima_diario.csv (Adriana)
data/raw/epidemiologia/*.csv (fuente oficial)
            ↓
1. Validación epidemiológica (COM-xx / EPI-xx)
            ↓
2. Calendario diario GLOBAL por municipio
   (corrige el riesgo de desfase por reindexado ad-hoc entre grupos)
            ↓
3. Imputación climática, en el orden que define reglas_calidad_datos.md §5.2:
   a) interpolación lineal (huecos ≤ 2 días)
   b) mediana histórica municipio+semana del año
   c) mediana del municipio vecino más cercano (por distancia real de estación)
   d) si nada aplica: se conserva como faltante
            ↓
4. Reagregación semanal con nivel de confianza (NFR-007: 0-5% / 5-20% / >20%)
            ↓
5. Resumen de calidad del lote (recibidos/válidos/imputados/rechazados)
```

### 2.1 Validación epidemiológica

Sobre `dengue_bolivia_municipal_SE01_13_2026.csv`,
`malaria_bolivia_municipal_SE01_13_2026.csv` y
`dengue_bolivia_semanal_SE01_13_2026.csv`:

- Rechaza municipios vacíos (COM-01), duplicados exactos municipio+año
  (COM-04) y casos negativos o no enteros (EPI-01).
- Verifica que ninguna columna corresponda a datos personales (EPI-05 /
  REQ-020) — si los hubiera, el pipeline se detiene en vez de continuar.
- La serie semanal nacional de dengue se marca `provisional`, no `válida`,
  porque la propia fuente declara ese dato como "sujeto a actualización" en
  cada fila (regla 6.2.4).
- **No imputa casos.** Un municipio ausente en el dataset de malaria (ej.
  Palos Blancos) se reporta como `sin_reporte`, nunca como cero (regla
  6.2.1/6.2.2).

### 2.2 Calendario diario global

`clima_diario.csv` tenía huecos reales de calendario: días completos sin
ninguna fila para un municipio (1 día en Guayaramerín e Ixiamas, 21 en
Palos Blancos, 27 en San Buenaventura, sobre 81 días de calendario
2026-01-14 a 2026-04-04). El riesgo ya documentado antes de este pipeline
era reindexar cada municipio por separado, lo que puede generar un desfase
de fila entre grupos. Aquí se construye un único calendario global
(mismo rango de fechas para los cuatro municipios) y se reindexa una sola
vez sobre ese eje común.

### 2.3 Imputación climática

Se aplica a `temperatura_media`, `humedad_media` y `precipitacion_24h`.
Cada valor final conserva:

- `<variable>_original`: el valor antes de imputar (o `NaN` si no existía).
- `<variable>_metodo`: `observado`, `interpolacion_lineal`,
  `mediana_municipio_vecino(<municipio>)`, `mediana_historica_...` o
  `faltante`.
- `<variable>_es_imputado`: booleano.

El vecino más cercano se calcula por distancia real (fórmula de Haversine)
entre las coordenadas de las estaciones SENAMHI, no por cercanía asumida:

| Municipio | Vecino usado | Distancia |
|---|---|---:|
| Guayaramerín | Ixiamas | 445.9 km |
| Ixiamas | San Buenaventura | 97.6 km |
| Palos Blancos | San Buenaventura | 127.9 km |
| San Buenaventura | Ixiamas | 97.6 km |

**Regla no aplicable con los datos actuales:** la mediana histórica por
semana del año (paso 2 de la regla) requiere más de un año de
observaciones; el dataset actual solo cubre 2026, así que este paso queda
documentado como no aplicable en vez de forzarse — el pipeline lo declara
explícitamente en `resumen_calidad_pipeline.json`, no lo oculta.

### 2.4 Reagregación semanal con nivel de confianza

Se recalcula el dataset semanal desde los datos ya imputados y se clasifica
cada fila municipio-semana según el % de días aún faltantes, usando los
umbrales de NFR-007:

| % faltante | Nivel |
|---:|---|
| 0–5% | `confianza_normal` |
| 5–20% | `confianza_baja` |
| >20% | `datos_insuficientes` (no se publicaría una predicción operativa) |

## 3. Resultado obtenido (última ejecución)

Antes de este pipeline (`docs/eda_inicial.md` §6), la cobertura semanal
suficiente era:

| Municipio | Semanas con cobertura suficiente (antes) |
|---|---:|
| Guayaramerín | 100.00% |
| Ixiamas | 100.00% |
| Palos Blancos | 54.55% |
| San Buenaventura | 27.27% |

Después de la imputación (44 filas municipio-semana evaluadas):

| Nivel de confianza | Filas |
|---|---:|
| `confianza_normal` | 43 |
| `confianza_baja` | 1 (Palos Blancos, SE3) |
| `datos_insuficientes` | 0 |

Ningún municipio queda en `datos_insuficientes`: la imputación resuelve la
mayoría de los huecos de calendario, y donde no puede (queda 1 día sin
resolver en total) el porcentaje resultante sigue siendo bajo. El detalle
completo, incluyendo qué método se usó por cada día y variable, queda en
`data/processed/clima_diario_imputado.csv`.

## 4. Reproducibilidad

### Comando

```bash
python3 scripts/limpieza_datos.py
```

Requiere las dependencias de `requirements.txt` (pandas, numpy) y que ya
existan `data/processed/clima_diario.csv` (generado por
`scripts/procesar_clima.py`) y los CSV crudos de `data/raw/epidemiologia/`
y `data/raw/clima/senamhi/`.

**Nota sobre DVC:** `data/raw/` está versionado con DVC contra un remoto en
DagsHub. Si al clonar el repositorio esas carpetas aparecen vacías o solo
con archivos `.dvc`, hay que pedir acceso de colaborador al repositorio de
DagsHub y correr `dvc pull -r origin-s3` antes de ejecutar este pipeline
(ver `docs/cierre_sprint1.md` §3.1 para el detalle de cómo se resolvió esto
la primera vez).

### Tiempo de ejecución

**~0.1–0.2 segundos** sobre el dataset actual (274 registros diarios de
clima, 28 filas de dengue municipal, 21 de malaria municipal, 13 semanas de
dengue nacional). No requiere red ni credenciales.

### Salida esperada

El script imprime por consola cada uno de los 5 pasos (validación,
calendario, imputación por variable, reagregación semanal, resumen) y
genera:

```text
data/processed/dengue_municipal_validado.csv
data/processed/malaria_municipal_validado.csv
data/processed/dengue_semanal_validado.csv
data/processed/clima_diario_imputado.csv
data/processed/clima_semanal_calidad.csv
data/processed/resumen_calidad_pipeline.md
data/processed/resumen_calidad_pipeline.json
```

`resumen_calidad_pipeline.md`/`.json` es el resumen de calidad del lote que
pide la sección 7 de `reglas_calidad_datos.md` (recibidos, válidos,
rechazados, provisionales, municipios sin reporte, reglas no aplicables).

## 5. Qué falta (honesto, no se oculta)

- La mediana histórica por semana del año no puede validarse hasta tener un
  segundo año de datos climáticos.
- La validación epidemiológica actual es estructural (tipos, rangos,
  duplicados, PII); no compara contra un catálogo oficial de municipios de
  Bolivia porque este proyecto no dispone aún de esa tabla de referencia
  (queda como pendiente de Ignacio/Ivonne en el inventario de datos).
- Los datos siguen siendo acumulados SE1-13 a nivel municipal para
  epidemiología, no series semana-a-semana por municipio. Este pipeline no
  resuelve esa limitación (ya documentada en `eda_inicial.md` §16); solo
  deja los datos disponibles en el mejor estado de calidad posible mientras
  esa limitación de fuente se resuelve.
