# Inventario de datos — Prediccion de brotes de dengue/malaria (Bolivia)

**Seccion del backlog:** Data
**Ultima actualizacion:** 2026-09-17
**Estado:** Actualizado post-EDA y pipeline de calidad
**Documentos relacionados:** `priorizacion_casos.md`, `product_goal.md`, `design.md` §10, `requirements.md` (REQ-013, REQ-014, REQ-015), `eda_inicial.md`, `pipeline_datos.md`, `reglas_calidad_datos.md`, `linea_base.md`

---

## 1. Objetivo de este inventario

Listar cada fuente de datos del proyecto SIPTB con su **forma de acceso**,
su **estado real de obtencion**, las **caracteristicas de los datos efectivamente
descargados/procesados** y su relacion con los requisitos. Este documento
refleja lo que se logro obtener y validar a traves de los EDA y el pipeline
de calidad, no solo la intencion original.

### Convenciones de estado

| Estado | Significado |
|---|---|
| **Obtenida y procesada** | Datos descargados, validados y presentes en `data/processed/`. Pipeline de calidad ejecutado. |
| **Obtenida (raw disponible)** | Datos descargados y versionados con DVC, pero requieren `dvc pull` para acceder localmente. |
| **Acordada (pendiente de descarga)** | Fuente y forma de acceso identificadas, pero los datos aun no se han descargado. |
| **Pregunta abierta** | Fuente no definida todavia (ver `design.md` §10). |
| **Pendiente de completar** | Existe indicio de la fuente, pero falta informacion de acceso/confirmacion. |

---

## 2. Fuentes de datos epidemiologicos

### 2.1 Ministerio de Salud y Deportes de Bolivia — Boletin Epidemiologico N.13, 2026

| Campo | Detalle |
|---|---|
| **Estado** | **Obtenida y procesada** |
| **Forma de acceso** | Descarga/extraccion del boletin oficial; datos estructurados en CSV |
| **Ubicacion en el repo** | `data/raw/epidemiologia/` (raw DVC) + `data/processed/` (procesados) |
| **Archivos raw** | `dengue_bolivia_semanal_SE01_13_2026.csv` (13 filas), `dengue_bolivia_municipal_SE01_13_2026.csv` (28 filas), `malaria_bolivia_municipal_SE01_13_2026.csv` (21 filas) |
| **Archivos procesados** | `dengue_municipal_validado.csv` (28 filas), `malaria_municipal_validado.csv` (21 filas), `dengue_semanal_validado.csv` (13 filas) |
| **Contenido** | Dengue: casos semanales nacionales y acumulados municipales SE 1-13. Malaria: `p_vivax`, `p_falciparum`, `mixta`, `total_malaria` por municipio/SEDES |
| **Cobertura** | Nacional; semanas epidemiologicas 1 a 13 de 2026 |
| **Formato** | CSV ya estructurado, con columnas de trazabilidad (`fuente`, `pagina_fuente`, `nota`) |
| **Calidad observada** | 0 valores faltantes y 0 duplicados. Pipeline de calidad: 28/28 dengue municipal validos, 21/21 malaria municipal validos, 13/13 dengue semanal provisionales (ver `resumen_calidad_pipeline.json`) |
| **Totales verificados** | Dengue SE 1-13: **341 casos**. Malaria SE 1-13: **1,615 casos** |
| **Requisitos** | REQ-013 (ingesta), REQ-015 (procedencia/fuente) |
| **Notas / limitaciones** | Datos **provisionales** sujetos a actualizacion. Los casos municipales estan como **acumulados SE1-13** (no serie semana-a-semana por municipio), lo que impide modelado temporal directo. En dengue municipal no se reconstruyo la semana municipal cuando la posicion de celdas vacias del PDF era ambigua. En malaria, el texto narrativo atribuye Ixiamas a La Paz pero la tabla lo muestra bajo Pando; se conserva la tabla y se documenta la inconsistencia. |


## 3. Fuentes de datos climaticos

### 3.1 SENAMHI — Servicio Nacional de Meteorologia e Hidrologia (WIS 2.0)

| Campo | Detalle |
|---|---|
| **Estado** | **Obtenida y procesada** |
| **Forma de acceso** | Descarga automatizada via WIS 2.0 (`scripts/descargar_senamhi.py`) |
| **Ubicacion en el repo** | `data/raw/clima/senamhi/` (raw DVC) + `data/processed/` (procesados) |
| **Archivo raw** | `senamhi_raw_SE01_13_2026.csv` (16,778 observaciones, ~2.88 MB) |
| **Variables descargadas** | Temperatura del aire, humedad relativa, precipitacion |
| **Cobertura temporal** | 14 de enero de 2026 al 4 de abril de 2026 (81 dias de calendario) |
| **Municipios con datos** | Guayaramerin, Ixiamas, Palos Blancos, San Buenaventura |
| **Registros tras control de calidad** | 16,754 registros validos (24 registros sospechosos de precipitacion extrema separados para validacion) |
| **Calidad observada** | Registros sospechosos: 24 (todos `precipitacion_extrema_requiere_validacion`). Resultado del control: `control_calidad_clima.csv` |

#### Archivos procesados generados

| Archivo | Contenido | Registros |
|---|---|---|
| `clima_diario.csv` | Serie diaria municipio-dia (temp, humedad, precip) | 274 registros municipio-dia |
| `clima_diario_imputado.csv` | Diario con imputacion y metadato de metodo | 324 registros (calendario global completo) |
| `clima_semanal.csv` | Agregacion semanal por municipio | 44 registros (4 municipios x 11 semanas) |
| `clima_semanal_calidad.csv` | Semanal con nivel de confianza NFR-007 | 44 registros |
| `control_calidad_clima.csv` | Resultado del QC sobre datos raw | 16,778 registros |

#### Cobertura diaria por municipio

| Municipio | Dias disponibles | Dias en calendario | Cobertura |
|---|---|---:|---|
| Guayaramerin | 80 | 81 | 98.77% |
| Ixiamas | 80 | 81 | 98.77% |
| Palos Blancos | 60 | 81 | 74.07% |
| San Buenaventura | 54 | 81 | 66.67% |

#### Nivel de confianza semanal (post-imputacion)

| Nivel | Filas |
|---|---:|
| `confianza_normal` (0-5% faltante) | 43 |
| `confianza_baja` (5-20% faltante) | 1 (Palos Blancos SE3) |
| `datos_insuficientes` (>20% faltante) | 0 |

#### Imputacion aplicada

El pipeline de limpieza (`scripts/limpieza_datos.py`) imputo los huecos de calendario usando:
1. Interpolacion lineal (huecos de 1-2 dias)
2. Mediana del municipio vecino mas cercano (distancia Haversine)

| Municipio | Vecino usado | Distancia |
|---|---|---:|
| Guayaramerin | Ixiamas | 445.9 km |
| Ixiamas | San Buenaventura | 97.6 km |
| Palos Blancos | San Buenaventura | 127.9 km |
| San Buenaventura | Ixiamas | 97.6 km |

**Regla no aplicable:** La mediana historica por semana del año requiere mas de un año de observaciones; el dataset actual solo cubre 2026.

#### Estadisticas climaticas por municipio (periodo SE3-SE13)

| Municipio | Temp media | Humedad media | Precip media/dia | Precip total acum |
|---|---:|---:|---:|---:|
| Guayaramerin | 26.61 C | 91.70% | 7.03 mm | -- |
| Ixiamas | 24.90 C | 89.33% | 11.81 mm | -- |
| Palos Blancos | 25.83 C | 92.37% | 6.16 mm | -- |
| San Buenaventura | 26.60 C | 91.43% | 0.18 mm | -- |

#### Correlaciones climaticas observadas (EDA climatico, Spearman, n=44)

| Par de variables | Coeficiente |
|---|---:|
| Temperatura - Humedad | -0.464 |
| Temperatura - Precipitacion | -0.411 |
| Humedad - Precipitacion | 0.059 |

#### Hallazgos clave del EDA climatico

- La relacion inversa temperatura-humedad es el patron mas consistente (Pearson: -0.80 a -0.96 por municipio).
- La precipitacion presenta mayor variabilidad, valores extremos y diferencias de cobertura entre municipios.
- Las relaciones climaticas NO son homogeneas entre municipios; mantener la dimension geografica es importante.
- Guayaramerin e Ixiamas tienen mejor cobertura climatica que Palos Blancos y San Buenaventura.

#### Requisitos

REQ-013 (ingesta), REQ-014 (nuevas fuentes sin rediseño), REQ-015 (procedencia/fuente)


---

---

## 4. Datasets procesados disponibles en el repositorio

Los siguientes archivos estan en `data/processed/` y son generados por los scripts del pipeline:

| Archivo | Origen | Registros | Uso principal |
|---|---|---|---|
| `dengue_municipal_validado.csv` | Validacion epidemiologica | 28 | Casos acumulados por municipio |
| `malaria_municipal_validado.csv` | Validacion epidemiologica | 21 | Malaria por municipio/SEDES |
| `dengue_semanal_validado.csv` | Validacion epidemiologica | 13 | Serie semanal nacional (provisional) |
| `clima_diario.csv` | `procesar_clima.py` | 274 | Serie diaria sin imputar |
| `clima_diario_imputado.csv` | `limpieza_datos.py` | 324 | Serie diaria imputada con metadatos |
| `clima_semanal.csv` | `procesar_clima.py` | 44 | Agregacion semanal basica |
| `clima_semanal_calidad.csv` | `limpieza_datos.py` | 44 | Semanal con nivel de confianza |
| `control_calidad_clima.csv` | `procesar_clima.py` | 16,778 | Resultado del QC sobre raw |
| `dataset_integrado_municipal.csv` | `integrar_datos.py` | 4 | Union clima + epidemiologia por municipio |
| `resumen_calidad_pipeline.json` | `limpieza_datos.py` | -- | Resumen de calidad del lote |
| `resumen_calidad_pipeline.md` | `limpieza_datos.py` | -- | Resumen legible de calidad |

---

## 5. Matriz resumen de estado

| # | Fuente | Tipo | Forma de acceso | Estado | Datos disponibles |
|---|---|---|---|---|---|
| 2.1 | Ministerio de Salud — Boletin N.13/2026 | Epidemiologico | Extraccion oficial a CSV | **Obtenida y procesada** | 341 casos dengue, 1,615 malaria (SE1-13) |
| 2.2 | SEDES | Epidemiologico | Solicitud formal por correo | Acordada (pendiente) | -- |
| 2.3 | SNIS | Epidemiologico | Por definir | Pregunta abierta | -- |
| 3.1 | SENAMHI WIS 2.0 | Climatico | Descarga automatizada (WIS 2.0) | **Obtenida y procesada** | 16,778 obs raw, 4 municipios, 81 dias |
| 3.2 | NASA POWER | Climatico | API publica | Pregunta abierta | -- |
| 3.3 | OPS/PAHO | Epidemiologico (validacion) | CSV descargable | Acordada (publica) | -- |
| 4.1 | INE | Poblacional/geografico | Por definir | Pendiente de completar | -- |

---

## 6. Integraciones logradas

### 6.1 Dataset integrado (clima + epidemiologia)

| Campo | Detalle |
|---|---|
| **Script** | `scripts/integrar_datos.py` |
| **Archivo** | `data/processed/dataset_integrado_municipal.csv` |
| **Municipios integrados (dengue + clima)** | 4: Guayaramerin, Ixiamas, Palos Blancos, San Buenaventura |
| **Municipios integrados (malaria + clima)** | 3: Guayaramerin, Ixiamas, San Buenaventura |
| **Unidad actual** | Municipio (acumulado, no serie temporal) |
| **Variables integradas** | Temp media, humedad media, precip media, casos dengue, incidencia, total malaria |
| **Limite clave** | Solo 4 (o 3) filas; no es un dataset temporal. Los casos estan acumulados SE1-13. |

### 6.2 Cobertura del dataset integrado

| Municipio | Cobertura climatica diaria | Semanas con cobertura suficiente | Cobertura climatica alta |
|---|---|---:|---|
| Guayaramerin | 98.77% | 100% | Si |
| Ixiamas | 98.77% | 100% | Si |
| Palos Blancos | 74.07% | 54.55% (6/11) | No |
| San Buenaventura | 66.67% | 27.27% (3/11) | No |

### 6.3 Epidemiologia por municipio integrado

| Municipio | Dengue acum. | Incidencia/10k | P. vivax | P. falciparum | Mixta | Total malaria |
|---|---:|---:|---:|---:|---:|---:|
| Guayaramerin | 9 | 2.2 | 199 | 87 | 7 | 293 |
| Ixiamas | 15 | 12.0 | 100 | 52 | 4 | 156 |
| Palos Blancos | 5 | 1.9 | -- | -- | -- | Sin dato |
| San Buenaventura | 22 | 21.7 | 1 | 0 | 0 | 1 |

### 6.4 Relaciones clima-enfermedad exploradas (EDA integrado)

| Variable climatica | Variable epidemiologica | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| Temperatura | Dengue | 4 | 0.116 | 0.000 |
| Temperatura | Incidencia dengue | 4 | 0.060 | 0.000 |
| Temperatura | Malaria | 3 | -0.029 | 0.500 |
| Humedad | Dengue | 4 | -0.447 | -0.800 |
| Humedad | Incidencia dengue | 4 | -0.389 | -0.800 |
| Humedad | Malaria | 3 | 0.068 | 0.500 |
| Precipitacion | Dengue | 4 | -0.432 | -0.200 |
| Precipitacion | Incidencia dengue | 4 | -0.483 | -0.200 |
| Precipitacion | Malaria | 3 | 0.614 | 0.500 |

**Interpretacion:** Estas correlaciones son exploratorias (n=3 o n=4). No constituyen evidencia predictiva ni causal. Se conservan como linea base para comparaciones futuras con mayor cantidad de observaciones municipio-semana.

---

## 7. Limitaciones conocidas

### 7.1 Limitaciones de datos epidemiologicos

1. **Casos acumulados, no serie temporal:** Los datos municipales estan como acumulados SE1-13. No hay serie semana-a-semana por municipio. Esto impide modelado temporal directo (variables rezagadas, prediccion t+k).
2. **Solo 4 municipios integrados:** La zona piloto esta limitada a municipios con datos coincidentes de clima y epidemiologia.
3. **Sin dato de malaria en Palos Blancos:** Reducido a 3 municipios para malaria.
4. **Datos provisionales:** El boletin declara los datos como sujetos a actualizacion.

### 7.2 Limitaciones de datos climaticos

1. **Un solo año (2026):** No es posible calcular medianas historicas por semana del año ni analizar estacionalidad inter-anual.
2. **Cobertura desigual:** Palos Blancos (74%) y San Buenaventura (67%) tienen menor cobertura que Guayaramerin e Ixiamas (99%).
3. **Periodo climático (SE3-SE13) no coincide completamente con epidemiologico (SE1-SE13):** SE1-SE2 no tienen datos climaticos.
4. **Solo 4 municipios:** Limitado a las estaciones SENAMHI con datos disponibles que coinciden con la zona piloto.

### 7.3 Limitaciones estructurales

1. **Sin tabla de referencia de municipios del INE:** No se puede validar contra catalogo oficial ni calcular incidencias propias.
2. **Dengue y malaria requieren modelos separados:** Los perfiles epidemiologicos son distintos (San Buenaventura lidera dengue; Guayaramerin lidera malaria).
3. **Correlaciones extremas (dengue-malaria: -1.000) son artefacto del tamaño de muestra:** Con n=3, los coeficientes son inestables.

---

## 8. Vacios de informacion pendientes

| # | Fuente | Que falta | Impacto |
|---|---|---|---|
| 1 | SENAMHI | Ampliar a mas años para estacionalidad | Medianas historicas, validacion de reglas de calidad |
| 2 | Epidemiologia | Obtener casos semana-a-semana por municipio (no acumulados) | **Critico:** sin esto no hay modelo temporal |

---

## 9. Trazabilidad con requisitos

| Requisito | Fuentes involucradas | Estado actual |
|---|---|---|
| REQ-013 (ingesta de datos) | 2.1, 3.1 | Implementada para Min. Salud y SENAMHI |
| REQ-014 (nuevas fuentes sin rediseño) | 2.2, 2.3, 3.1, 3.2 | Pendiente: SEDES, SNIS, NASA POWER |
| REQ-015 (procedencia/fuente + fecha de ingesta) | 2.1 (columnas `fuente`), 3.1 (script automatizado) | Cumplida para fuentes obtenidas |

---

## 10. Evidencias generadas

### 10.1 EDA inicial

- **Script:** `scripts/eda_inicial.py`
- **Salida:** `scripts/eda_output/` (6 CSVs, multiple PNGs)
- **Documento:** `docs/eda_inicial.md` (1,216 lineas)

### 10.2 EDA climatico

- **Script:** `scripts/eda_climatico.py`
- **Salida:** `scripts/eda_climatico_output/` (~50 archivos: CSVs, PNGs, 1 TXT)
- **Resumen:** `resumen_eda_climatico.txt`

### 10.3 EDA integrado

- **Script:** `scripts/eda_integrado.py`
- **Salida:** `scripts/eda_integrado_output/` (~35 archivos: CSVs, PNGs, 1 TXT)
- **Archivos clave:** `resumen_integrado.csv`, `correlaciones_clima_enfermedad.csv`, `comparacion_municipios_integrada.csv`

### 10.4 Linea base

- **Script:** `scripts/linea_base_modelo.py`
- **Salida:** `scripts/linea_base_output/` (4 CSVs, 2 JSONs, 1 PNG)
- **Documento:** `docs/linea_base.md`
- **Resultado:** Referencia nacional (serie temporal 13 semanas) contra baselines B0-B3; modelo municipal no entrenable aun (4 filas).

---

## 11. Reproducibilidad

Para reproducir el flujo completo de datos:

```bash
python scripts/descargar_senamhi.py      # Descarga SENAMHI (requiere red)
python scripts/procesar_clima.py         # QC + diario + semanal
python scripts/eda_inicial.py            # EDA epidemiologico
python scripts/eda_climatico.py          # EDA climatico
python scripts/limpieza_datos.py         # Pipeline de calidad + imputacion
python scripts/integrar_datos.py         # Union clima + epidemiologia
python scripts/eda_integrado.py          # EDA integrado
python scripts/linea_base_modelo.py      # Experimentos baseline
```

**Nota DVC:** Los datos raw estan versionados con DVC contra DagsHub. Si las carpetas `data/raw/` estan vacias, ejecutar `dvc pull -r origin-s3` con credenciales de DagsHub.

---

> **Regla de evidencia:** Este inventario refleja exclusivamente datos
> obtenidos, procesados y verificados. Los volumenes y accesos marcados
> como "referencial" provienen de `priorizacion_casos.md` y `design.md §10`;
> no se citan como confirmados hasta completar el acceso.
