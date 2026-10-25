# Contrato de esquema de datos procesados

**Define:** Tania Perez — Frente "Pipeline de datos"
**Usan (en paralelo, sin esperar):** Adriana (modelo XGBoost + SHAP), Dilan (pruebas)
**Publicado:** 2026-10-25 (día 1 del reparto "Reparto_de_Desarrollo_MVP_Paralelo")
**Cómo se genera:** `python scripts/pipeline_completo.py` (ver [`pipeline_de_datos.md`](./pipeline_de_datos.md))
**Cómo se valida:** `python scripts/validar_contrato.py` · **Guía de arranque para la Fase 2:** [`guia_entrega_fase2.md`](./guia_entrega_fase2.md)

---

## 1. Qué es este documento

El contrato "Esquema de datos procesados" del reparto del equipo: los
nombres y tipos de columnas de cada dataset final, para que Adriana pueda
entrenar el modelo y Dilan pueda escribir pruebas **sin esperar** a que el
pipeline termine de ejecutarse — ambos construyen contra este esquema desde
hoy, con los archivos de ejemplo ya presentes en `data/processed/`.

Regla: si un cambio en el pipeline modifica una columna de aquí (nombre,
tipo o significado), ese cambio se anuncia al equipo y este documento se
actualiza en el mismo commit — nunca al revés.

## 2. Alcance y limitaciones que aplican a TODOS estos archivos

- **Dos zonas de datos distintas:**
  - *Piloto SENAMHI* (§3-§7): 4 municipios (GUAYARAMERIN, IXIAMAS,
    PALOS BLANCOS, SAN BUENAVENTURA), únicos con estación real. Clima SE3-13.
  - *Ampliada* (§7bis en adelante): los 28 municipios con dengue y los 22
    con malaria, con clima de reanálisis NASA POWER. Es la que debe usar el modelo.
- **Epidemiología:** dengue tiene serie semanal real por municipio
  (SE1-13 de 2026). Malaria **no**: solo acumulados SE1-k por boletín, de
  los que se reconstruyen bloques de semanas (ver §7bis).
- **Un solo año, 13 semanas:** no hay historia de años anteriores.
- Un valor ausente nunca se interpreta como cero; se marca explícitamente
  (`es_dato_imputado`, `estado_calidad == 'sin_reporte'`, `ausente_en_boletin`, etc.).

## 3. `data/processed/clima_diario_imputado.csv`

Clima diario por municipio, ya imputado (interpolación → mediana histórica
→ municipio vecino → faltante).

| Columna | Tipo | Significado |
|---|---|---|
| `municipio` | texto | Nombre en mayúsculas, uno de los 4 piloto. |
| `fecha` | fecha | Día calendario (calendario global, sin huecos de fila). |
| `temperatura_media` / `humedad_media` / `precipitacion_24h` | numérico | Valor ya imputado (nunca NaN si alguna regla de imputación aplicó). |
| `{variable}_original` | numérico | Valor crudo antes de imputar (puede ser NaN). |
| `{variable}_metodo` | texto | `observado`, `interpolacion_lineal`, `mediana_historica_municipio_semana`, `mediana_municipio_vecino(...)` o `faltante`. |
| `{variable}_es_imputado` | booleano | `True` si el método no fue `observado` ni `faltante`. |

## 4. `data/processed/clima_semanal_calidad.csv`

Clima reagregado a nivel semanal, con nivel de confianza (NFR-007).

| Columna | Tipo | Significado |
|---|---|---|
| `municipio`, `anio`, `semana_epidemiologica` | texto/entero | Clave de la fila. |
| `temperatura_media`, `humedad_media`, `precipitacion_total_mm` | numérico | Agregado semanal (media o suma según variable). |
| `dias_en_semana` | entero | Días de calendario cubiertos por esa semana. |
| `dias_{variable}_imputados` | entero | Cuántos de esos días fueron imputados. |
| `dias_faltantes` | entero | Días sin ningún valor de temperatura tras imputar. |
| `porcentaje_faltante` | numérico | `dias_faltantes / dias_en_semana * 100`. |
| `nivel_confianza` | texto | `confianza_normal` (≤5%), `confianza_baja` (5-20%) o `datos_insuficientes` (>20%) — umbrales de NFR-007. |

## 5. `data/processed/clima_semanal_ventanas.csv` — NUEVO (ventanas temporales)

Mismas columnas que el archivo anterior, más las ventanas temporales que
usa el modelo:

| Columna | Tipo | Significado |
|---|---|---|
| `{variable}_lag{1..4}` | numérico | Valor de esa variable hace 1 a 4 semanas, mismo municipio. `NaN` si no hay esa historia. |
| `{variable}_media_movil_{2,3,4}sem` | numérico | Promedio móvil de las últimas 2/3/4 semanas (incluye la actual), solo con semanas pasadas — nunca mira al futuro. |
| `semanas_historia_disponible` | entero | Cuántas semanas de historia tiene esa fila dentro de su municipio. |
| `ventana_completa_4_semanas` | booleano | `True` si ya hay las 4 semanas de historia que pide `design.md` (lag 2-4 semanas). |

## 6. `data/processed/dengue_municipal_validado.csv` y `malaria_municipal_validado.csv`

Un registro por municipio boliviano (no solo los 4 piloto), acumulado
SE1-13 de 2026, validado contra `docs/reglas_calidad_datos.md`.

| Columna | Tipo | Significado |
|---|---|---|
| `municipio`, `departamento`, `anio` | texto/entero | Identificación. |
| `casos_dengue_acumulados_se1_13` (dengue) / `total_malaria` (malaria) | entero | El acumulado real reportado por la fuente — NUNCA una cifra semanal. |
| `estado_calidad` | texto | `valido` o `rechazado`. **Filtrar siempre por `valido` antes de usar.** |
| `regla_aplicada`, `motivo_qc` | texto | Por qué se rechazó, si aplica (vacío si es válido). |
| `fuente` | texto | Ministerio de Salud y Deportes de Bolivia, Boletín Epidemiológico N.º 13. |

## 7. `data/processed/dataset_integrado_municipal.csv` (agregación por zona)

Una fila por municipio piloto (4 filas), clima agregado sobre todo el
periodo + el acumulado epidemiológico — el dataset "cross-sectional" que
usan los Experimentos C/D de `docs/resultados_linea_base.md`.

| Columna | Tipo | Significado |
|---|---|---|
| `municipio` | texto | Uno de los 4 piloto. |
| `temperatura_media_periodo`, `humedad_media_periodo`, `precipitacion_total_periodo_mm`, etc. | numérico | Agregados del periodo completo (no semanales). |
| `cobertura_climatica_alta` | booleano | `True` si ≥ cierto umbral de semanas con cobertura suficiente. |
| `casos_dengue_acumulados_se1_13`, `total_malaria` | numérico | Target epidemiológico (acumulado, no semanal). `NaN` en malaria para el municipio sin reporte — no es cero. |
| `dengue_disponible`, `malaria_disponible` | booleano | Si ese municipio tiene reporte para esa enfermedad. |
| `alineacion_temporal_completa` | booleano | Siempre `False` en esta versión — clima es SE3-13 y epidemiología SE1-13, no coinciden del todo (ver `nota_integracion`). |

**Advertencia para quien entrene con este archivo (n=4):** ver
`docs/resultados_linea_base.md` Experimento C — con 4 filas y 3+ variables
el modelo sobreajusta (R²=1.0, 0 grados de libertad). No es un error de
este contrato, es el tamaño real de la muestra piloto.

## 7bis. `data/processed/dengue_municipal_semanal.csv` y `panel_semanal_dengue_clima.csv` — NUEVO (serie semanal real)

**Hallazgo de sesión 2026-10-25:** el Boletín Epidemiológico N°13 del
Ministerio de Salud SÍ trae dengue desglosado por semana y municipio
(columnas SE1 a SE13), algo que el pipeline original no extraía — solo
tomaba la columna "Total". Esto resuelve el vacío documentado en
`docs/inventario_datos.md` §8 ("Crítico: sin esto no hay modelo
temporal"), **solo para dengue** (ver advertencia abajo).

### `dengue_municipal_semanal.csv` (formato largo, 364 filas = 28 municipios × 13 semanas)

| Columna | Tipo | Significado |
|---|---|---|
| `departamento`, `municipio`, `anio` | texto/entero | Identificación (heredada de `dengue_municipal_validado.csv`). |
| `semana_epidemiologica` | entero 1-13 | Semana del año. |
| `casos_dengue` | entero | Casos confirmados **de esa semana específica** (no acumulado). Verificado automáticamente: la suma por semana y el total general coinciden exacto con el boletín impreso. |
| `fuente`, `pagina_fuente`, `periodo_dato` | texto | Trazabilidad. |

### `panel_semanal_dengue_clima.csv` — **v2** (364 filas = 28 municipios × 13 semanas)

El dataset para entrenar el modelo de **dengue**. Una fila por municipio-semana.

> **Cambio de contrato respecto a la v1 (52 filas, 4 municipios).** Se anuncia
> al equipo en el mismo commit. Las columnas de clima conservan su nombre
> pero ahora vienen de **NASA POWER** para los 28 municipios; SENAMHI pasó a
> columnas `senamhi_*`. Se eliminaron del panel las columnas
> `dias_*_imputados`, `dias_faltantes`, `porcentaje_faltante`, `nivel_confianza`,
> `dias_en_semana`, `semanas_historia_disponible` y `ventana_completa_4_semanas`
> (eran propias de SENAMHI y siguen en `clima_semanal_calidad.csv` /
> `clima_semanal_ventanas.csv`).

| Columna(s) | Tipo | Significado |
|---|---|---|
| `departamento`, `municipio`, `anio`, `semana_epidemiologica` | — | Clave de la fila (SE 1-13 de 2026). |
| `casos_dengue` | entero | Casos confirmados de **esa** semana. |
| `fuente`, `pagina_fuente`, `periodo_dato` | texto | Trazabilidad del dato de casos. |
| `temperatura_media`, `humedad_media`, `precipitacion_total_mm` | numérico | Clima semanal NASA POWER (precipitación = suma semanal en mm). Sin NaN: los 364 registros tienen clima. |
| `{variable}_lag{1-4}`, `{variable}_media_movil_{2,3,4}sem` | numérico | Rezagos y medias móviles calculados sobre la serie completa desde oct-2025, por eso **no hay NaN** en SE1-SE4. |
| `fuente_clima`, `tiene_clima` | texto / booleano | `NASA POWER (reanalisis)` / `True`. |
| `senamhi_temperatura_media`, `senamhi_humedad_media`, `senamhi_precipitacion_total_mm`, `senamhi_cobertura_suficiente` | numérico / booleano | Estación real SENAMHI. Solo 4 municipios y SE3-13 (44 filas); `NaN` en el resto. **No usar como predictor común**: solo para comparar. |
| `casos_dengue_lag{1-4}` | numérico | Casos de las semanas anteriores del mismo municipio. `NaN` al inicio de la serie (no hay 2025). |
| `casos_dengue_acum_4sem` | numérico | Suma de las 4 últimas semanas (incluye la actual). |
| `casos_dengue_t_mas_3`, `casos_dengue_t_mas_4` | numérico | **Candidatos a variable objetivo**: casos 3 y 4 semanas después (el horizonte del producto). `NaN` en las últimas 3-4 semanas de cada municipio. |
| `hay_casos_t_mas_3` | booleano | `casos_dengue_t_mas_3 > 0`. Marca neutra; **no es una definición de brote** (eso lo define la Fase 2). |

Filas utilizables para predecir a 3 semanas (con `casos_dengue_lag1` y
`casos_dengue_t_mas_3`): **252**. De ellas, solo 96 tienen casos > 0 en el
objetivo, y San Borja (140 casos) y Caranavi (60) concentran la mayoría.

**Límites reales que debe conocer quien entrene:**
- **Una sola estación incompleta:** 13 semanas de un solo año (ene-mar 2026,
  época de lluvias). No hay ciclo anual ni validación entre años. Las
  métricas sirven para probar el código, no como evidencia de desempeño.
- **Desbalance fuerte:** muchos municipios tienen 0-3 casos en total.
- **Los datos recientes se corrigen después** (ver
  `dengue_revisiones_resumen.csv` abajo): en producción el último dato de
  casos estará subestimado, así que `casos_dengue_lag1` se verá más bajo de
  lo que verá el modelo entrenado con el dato final.
- **Un municipio ausente de la tabla de dengue no se rellena con ceros**: se
  desconoce si no tuvo casos o no reportó (14 municipios con malaria no
  aparecen en dengue).
- **Clima NASA POWER es modelado, no observado.** Contra SENAMHI (31
  semanas con cobertura suficiente, 4 municipios): temperatura r=0,69 y sesgo
  −1,3 °C; humedad r=0,24 y sesgo −2,0 pts; precipitación semanal r=0,40 y
  error medio absoluto 32 mm (la media es 53 mm). Sirve para temperatura;
  la lluvia semanal es una aproximación pobre. La resolución es ~0,5°, así
  que municipios vecinos (p. ej. Rurrenabaque y San Buenaventura) comparten
  celda y tienen clima idéntico.
- **Semana ISO (lunes-domingo)** como aproximación de la semana
  epidemiológica (domingo-sábado), igual que `procesar_clima.py`: desfase de 1 día.

### Archivos nuevos de apoyo (2026-10-25)

| Archivo | Contenido |
|---|---|
| `data/reference/municipios_coordenadas.csv` | Latitud/longitud de los 42 municipios (OpenStreetMap/Nominatim, ODbL) con la consulta y el `display_name` devueltos para auditar. Se genera una vez con `scripts/geocodificar_municipios.py` y se versiona; el pipeline solo lo lee. |
| `data/processed/clima_nasa_power_semanal.csv` | Clima semanal NASA POWER, 42 municipios, desde oct-2025. Clave: `municipio, anio, semana_epidemiologica`. Crudo diario en `data/raw/clima/nasa_power/` (cacheado: el pipeline no necesita red si existe). |
| `data/processed/malaria_acumulado_por_boletin.csv` | Acumulado de malaria SE1-k por municipio en los boletines SE5, 7, 8, 9 y 13. Con `fila_inconsistente` y `suma_coincide_total`. |
| `data/processed/malaria_municipal_bloques.csv` | Casos de malaria por **bloque** de semanas (diferencia entre cortes). |
| `data/processed/panel_bloques_malaria_clima.csv` | Bloques de malaria + clima del bloque y de las 4 semanas previas. |
| `data/processed/dengue_revisiones_boletines.csv` / `dengue_revisiones_resumen.csv` | Cuánto cambió cada celda municipio-semana entre un boletín y el SE13. |

### `panel_bloques_malaria_clima.csv` (103 filas = 22 municipios × bloques)

**Malaria no tiene serie semanal por municipio** en ninguna fuente que tengamos.
Se reconstruyen **bloques** restando acumulados de boletines consecutivos:
SE1-5, SE6-7, SE8, SE9 y SE10-13. Solo SE8 y SE9 son semanas individuales
(40 filas); el resto son bloques de varias semanas (63 filas). **Un bloque no
se reparte en semanas.**

| Columna(s) | Tipo | Significado |
|---|---|---|
| `municipio`, `anio`, `se_inicio`, `se_fin`, `n_semanas` | — | Clave y largo del bloque. |
| `tipo_bloque` | texto | `semana_exacta` o `bloque_varias_semanas`. |
| `casos_vivax`, `casos_falciparum`, `casos_mixta`, `casos_total` | numérico | Casos del bloque. `NaN` si el bloque no es utilizable. |
| `casos_por_semana` | numérico | `casos_total / n_semanas`. **Usar esta** para comparar bloques de distinto largo. |
| `revision_negativa` | booleano | El acumulado bajó entre boletines (la fuente revisó a la baja). Hoy: 0. |
| `fila_inconsistente` | booleano | Vivax+falciparum+mixta ≠ total en el boletín impreso (San Buenaventura, SE5). Esos bloques quedan sin casos. |
| `primer_acumulado` | booleano | Primer corte en que aparece el municipio: cubre SE1-k completo. |
| `temperatura_media_bloque`, `humedad_media_bloque`, `precipitacion_semanal_mm_bloque` | numérico | Clima NASA POWER promedio del bloque (la lluvia es mm por semana). |
| `*_previas4` | numérico | Mismo clima, promedio de las 4 semanas **anteriores** al bloque (lo que el modelo conoce de antemano). |

101 de 103 bloques son utilizables. Los casos se reportan **en tandas**: p. ej.
Ixiamas tiene 0 casos en SE6-7 y SE8, y 20 en SE9, lo que sugiere reporte
atrasado más que ausencia de casos.

### `dengue_revisiones_resumen.csv`

| `corte_boletin` | % del dato final (SE13) que **faltaba** en ese boletín |
|---|---|
| SE5 | 35 % |
| SE7 | 24 % |
| SE8 | 16 % |
| SE9 | 13 % |

Según la antigüedad de la semana (boletines SE7-9): la semana más reciente
muestra solo ~39 % de sus casos finales, la de hace 1 semana ~77 %, y desde 2
semanas atrás ~95 %. Los boletines SE3 y SE6 se descartaron automáticamente
porque su tabla no pasó la verificación contra el total impreso.

## 8. Cómo regenerar todo

```bash
python scripts/pipeline_completo.py
```

Ver [`pipeline_de_datos.md`](./pipeline_de_datos.md) para el detalle de
cada paso y qué pasa si faltan los crudos de `data/raw/` (bloqueo de DVC).
