# Contrato de esquema de datos procesados

**Define:** Tania Perez — Frente "Pipeline de datos"
**Usan (en paralelo, sin esperar):** Adriana (modelo XGBoost + SHAP), Dilan (pruebas)
**Publicado:** 2026-10-25 (día 1 del reparto "Reparto_de_Desarrollo_MVP_Paralelo")
**Cómo se genera:** `python scripts/pipeline_completo.py` (ver [`pipeline_de_datos.md`](./pipeline_de_datos.md))

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

## 2. Zona piloto y limitaciones que aplican a TODOS estos archivos

- **Zona piloto (4 municipios):** GUAYARAMERIN, IXIAMAS, PALOS BLANCOS,
  SAN BUENAVENTURA — únicos con cruce real de clima + epidemiología.
- **Clima:** resolución semanal real, 11 semanas (SE3-SE13 de 2026).
- **Epidemiología (dengue/malaria):** un único acumulado por municipio
  para todo el periodo SE1-13 — **no existe una serie semana a semana**
  (ver `docs/resultados_linea_base.md`, Experimentos C y D). Ningún
  archivo de esta lista inventa esa granularidad.
- Un valor ausente nunca se interpreta como cero; se marca explícitamente
  (`es_dato_imputado`, `estado_calidad == 'sin_reporte'`, etc.).

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

## 8. Cómo regenerar todo

```bash
python scripts/pipeline_completo.py
```

Ver [`pipeline_de_datos.md`](./pipeline_de_datos.md) para el detalle de
cada paso y qué pasa si faltan los crudos de `data/raw/` (bloqueo de DVC).
