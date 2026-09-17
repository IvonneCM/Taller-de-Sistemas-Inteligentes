# EDA Inicial — Sistema de Predicción Temprana de Brotes de Dengue/Malaria

**Responsable:** Adriana Rocha Vedia
**Sección del backlog:** Data
**Estado de los datos reales:** aún no confirmados/descargados (ver `priorizacion_casos.md`)

---

## 1. Por qué este documento incluye una justificación técnica y no solo resultados

Al momento de esta evaluación no contamos con acceso confirmado a los datos
reales:

- **SENAMHI** (clima): descarga directa disponible (~30 min) o vía solicitud
  por correo (3-5 días hábiles). Aún no descargado.
- **SEDES La Paz** (casos de dengue/malaria): requiere solicitud formal por
  correo a `epidemiologia@sedes.lapaz.gob.bo`, con plazo de respuesta de
  3-7 días hábiles. Solicitud aún no enviada/confirmada al cierre de esta
  entrega.
- **OPS/PAHO**: fuente pública de validación regional, disponible en CSV.

Siguiendo la regla de evidencia de la guía de defensa, este documento no deja
el punto en blanco: presenta el **pipeline de perfilado ya construido y
probado** (`eda_inicial.py`) corriendo sobre un dataset sintético que replica
las características documentadas de ambas fuentes, de forma que al llegar los
datos reales el mismo script se ejecuta sin cambios estructurales — solo se
reemplaza la función de carga por el conector real de `app/etl/conectores/`.

## 2. Supuestos usados para el dataset sintético

El dataset sintético no busca simular casos reales; busca **estresar el
pipeline de perfilado** contra los riesgos de datos ya identificados por el
equipo en `requirements.md` §5 y `priorizacion_casos.md`, además de inyectar
una señal causal controlada (clima con rezago → casos) para poder demostrar
el análisis de relación entre variables que pide esta entrega:

| Característica real documentada | Cómo se refleja en el dataset sintético |
|---|---|
| Cobertura irregular de estaciones SENAMHI en zonas rurales | Municipios rurales (Apolo, Ixiamas, Guanay, San Buenaventura) reciben una probabilidad de día-sin-registro de 25%, vs. 3% en zonas urbanas |
| Sesgo de vigilancia (zonas con mejor infraestructura reportan más) | Los municipios rurales generan casos epidemiológicos con un factor de reporte de 0.4x respecto al mismo nivel real de incidencia |
| Hipótesis del proyecto: el clima anticipa brotes | Los casos de una semana se generan a partir de la temperatura y precipitación de **3 semanas antes** (lag), más ruido de Poisson — para poder validar que el pipeline de EDA detecta esta relación |
| Retraso de reporte epidemiológico | Datos agregados semanalmente en vez de diariamente, como espera el SEDES |
| Formato semi-estructurado de SEDES (PDFs → Excel) | Se documenta como riesgo de calidad de datos, no se simula el parseo (fuera del alcance del EDA) |
| Errores de sensor / outliers climáticos | 0.5% de registros de temperatura con desviaciones de ±15-20°C respecto a la media |

## 3. Resultados del perfilado (sobre dataset sintético)

Ejecutando `eda_inicial.py`:

- **8,593 registros climáticos** y **1,368 registros epidemiológicos**
  generados sobre el rango 2024-01-01 a 2026-08-31 y 10 municipios de
  ejemplo (zona piloto tentativa: La Paz — pendiente confirmación oficial,
  ver `design.md` §10).
- **Faltantes por municipio**: los 4 municipios rurales muestran entre 23%
  y 28% de días sin registro climático, frente a ~3% en zonas urbanas —
  consistente con NFR-007 (tolerancia hasta 20% de datos faltantes; los
  municipios rurales superan ese umbral y deberían marcarse con
  `nivel_confianza = bajo` en las predicciones, según define `design.md`
  §5, paso 2).
- **Outliers de temperatura**: 94 registros detectados por método IQR,
  candidatos a revisión antes de imputación (ver `outliers_climaticos.csv`).
- **Distribuciones**: temperatura y humedad aproximadamente normales;
  precipitación con cola larga (muchos días sin lluvia, típico de datos
  pluviométricos); casos confirmados con forma tipo Poisson.
- **Matriz de correlación** (clima con 3 semanas de rezago vs. casos):
  la temperatura rezagada muestra la correlación más fuerte con los casos
  confirmados (**r = 0.29**); humedad y precipitación muestran correlación
  débil en este dataset sintético (ver `matriz_correlacion.csv` y
  `matriz_correlacion.png`).
- **Dispersión clima vs. casos**: el gráfico de regresión confirma
  visualmente la tendencia positiva entre temperatura rezagada y casos
  (`dispersion_clima_vs_casos.png`) — este es el tipo de relación que el
  motor de predicción (design.md §5) debe capturar vía feature engineering
  con variables rezagadas.
- **Boxplots por municipio**: además de exponer outliers, evidencian
  visualmente el **sesgo de vigilancia** — los municipios rurales muestran
  cajas de casos confirmados sistemáticamente más bajas que las urbanas,
  pese a compartir un rango climático similar (`boxplots_por_municipio.png`).
- **Serie temporal**: los casos totales muestran estacionalidad visible a
  lo largo del periodo simulado (`serie_temporal_casos.png`).

## 4. Qué cambia cuando lleguen los datos reales

1. Reemplazar `generar_datos_climaticos_sinteticos()` por el conector real
   de SENAMHI (`app/etl/conectores/senamhi.py`, pendiente de crear).
2. Reemplazar `generar_datos_epidemiologicos_sinteticos()` por el conector
   real de SEDES, incluyendo el paso de parseo PDF → estructurado que no
   está cubierto en esta versión sintética.
3. Re-ejecutar el mismo pipeline de perfilado (faltantes, outliers,
   distribuciones, correlación, dispersión) sin cambios de código.
4. Confirmar si el umbral de 20% de faltantes rurales (NFR-007) se sostiene
   con datos reales, y si la correlación clima-casos observada aquí (nivel
   de referencia: r≈0.29 con lag de 3 semanas) se mantiene, sube o baja con
   datos reales — esto informará directamente qué variables priorizar en
   `app/ml/features.py`.

## 5. Archivos de evidencia

- `eda_inicial.py` — script reproducible (ejecutar con `python eda_inicial.py`)
- `docs_eda_output/resumen_climatico.csv`
- `docs_eda_output/resumen_epidemiologico.csv`
- `docs_eda_output/outliers_climaticos.csv`
- `docs_eda_output/matriz_correlacion.csv`
- `docs_eda_output/faltantes_por_municipio.png`
- `docs_eda_output/distribucion_variables.png`
- `docs_eda_output/boxplots_por_municipio.png`
- `docs_eda_output/matriz_correlacion.png`
- `docs_eda_output/dispersion_clima_vs_casos.png`
- `docs_eda_output/serie_temporal_casos.png`