# TASK-013: evidencia real SHAP para la segunda defensa de GatoByte

## Objetivo y método

TASK-013 explica cada predicción de XGBoost mediante contribuciones locales
SHAP. Se utiliza `TreeExplainer` sobre los Booster reales de Ivonne, con
`model_output="raw"` y `feature_perturbation="tree_path_dependent"`.
La referencia se obtiene de las frecuencias de entrenamiento de las rutas
de los árboles; no se introduce un dataset simulado de fondo.

Los pesos positivos elevan el margen respecto al valor base y los negativos
lo reducen. La escala es **log-odds**, no porcentajes. La sigmoide del margen
completo produce la probabilidad de al menos un caso de dengue en t+h.
No se aplica la sigmoide a cada peso por separado.

## Modelos, datos y observación

- Modelos: `dengue-malaria-prediccion/app/ml/artifacts/baseline_dengue_t3_v1.json`
  y `baseline_dengue_t4_v1.json`, con sus metadatos v1.
- Dataset: `data/processed/panel_semanal_dengue_clima.csv`.
- Pipeline: `app.ml.features.cargar_features()` (TASK-011).
- Explicaciones: `app.ml.explicabilidad.explicar_observaciones()` (TASK-013).
- Observación local: **Alto Beni, 26 de enero de 2026**, con 24 features sin NaN.
- Se verificó identidad y orden de las 24 columnas entre pipeline, metadatos
  y Booster. Los nombres originales de las variables se conservan en las imágenes.
- No se entrenó ningún modelo ni se modificaron las fuentes.

Los beeswarm utilizan **252 observaciones reales**, de 28 municipios, entre 2026-01-26 y 2026-03-23. Se seleccionan filas con las 24 features disponibles: 112 filas del panel quedan fuera por historia o valores incompletos. Se usa exactamente el mismo subconjunto para ambos horizontes; no se exige objetivo futuro porque se describe el modelo, no se evalúa su acierto.

## Resultados numéricos y aditividad

| Métrica | t+3 | t+4 |
|---|---:|---:|
| Probabilidad de al menos un caso | 4.903647 % | 18.941328 % |
| Valor base (log-odds) | -0.6318929195 | -0.6962922812 |
| Salida real / margen (log-odds) | -2.9649114609 | -1.4538270235 |
| Suma de los 24 pesos | -2.3330165113 | -0.7575346367 |
| Base + suma de pesos | -2.9649094308 | -1.4538269178 |
| Error absoluto local | 2.030e-06 | 1.057e-07 |
| Error máximo del lote | 2.030e-06 | 3.248e-06 |

**Aditividad: OK en ambos horizontes y en todas las filas analizadas.** Se verifica `base + suma(24 pesos) ≈ margen` con `rtol=1e-5` y `atol=1e-5`. Las pequeñas diferencias son de precisión numérica. También se verifica que la sigmoide del margen coincide con `predecir_probabilidad()`.

### Cinco contribuciones locales principales: t+3

| Variable | Peso (log-odds) |
|---|---:|
| `temperatura_media_lag3` | -0.3188492060 |
| `precipitacion_total_mm_media_movil_4sem` | -0.2834830582 |
| `casos_dengue_media_movil_2sem` | -0.2823713422 |
| `humedad_media_media_movil_4sem` | -0.2523247004 |
| `precipitacion_total_mm_lag3` | -0.2075929940 |

### Cinco contribuciones locales principales: t+4

| Variable | Peso (log-odds) |
|---|---:|
| `temperatura_media_lag2` | -0.4824408293 |
| `casos_dengue_media_movil_2sem` | -0.4036886692 |
| `temperatura_media_lag3` | +0.2828623354 |
| `precipitacion_total_mm_lag2` | +0.2678293288 |
| `humedad_media_lag2` | +0.2667871714 |

## Lectura de las visualizaciones

### Waterfall: del valor base a la salida local

Incluyen las 24 contribuciones: las mayores se muestran individualmente y
las restantes se suman en una barra. El extremo final corresponde al margen,
no a la probabilidad. En t+3 las cinco mayores contribuciones reducen el margen;
en t+4 hay contribuciones de ambos signos.

![Waterfall t+3](shap/waterfall_t3.png)

![Waterfall t+4](shap/waterfall_t4.png)

### Barras: importancia local con signo

Muestran las 10 mayores contribuciones absolutas de Alto Beni, con sus signos
y valores numéricos. Azul reduce y rojo eleva el margen. No representan
importancia global ni incluyen la suma de las 14 variables omitidas.

![Contribuciones locales t+3](shap/importancia_t3.png)

![Contribuciones locales t+4](shap/importancia_t4.png)

### Beeswarm: distribución de explicaciones en el subconjunto

Cada punto representa una observación y cada fila una feature. La posición
horizontal es su contribución y el color representa su valor bajo/alto.
Las filas se ordenan por media de |SHAP| en el subconjunto. Este resumen
agregado describe esas observaciones; no es el ranking local de Alto Beni
ni una importancia global universal. Se muestran las 24 features.

![Beeswarm t+3](shap/summary_t3.png)

![Beeswarm t+4](shap/summary_t4.png)

### Comparación de horizontes

Compara los pesos locales sobre una escala común log-odds para las 10 features
con mayor máximo |SHAP| entre ambos modelos. Los colores identifican horizontes;
el signo indica dirección. Las bases son distintas y no se comparan aquí
probabilidades con contribuciones. Las diferencias describen dos modelos,
no un efecto temporal causal de una variable.

![Comparación de contribuciones t+3 y t+4](shap/comparacion_t3_t4.png)

## Correspondencia entre gráficas y cifras

Todas las gráficas usan la misma matriz de contribuciones devuelta por TASK-013,
reconstruida por nombre en el orden exacto del artefacto. No se copiaron pesos
manualmente. Waterfall recibe las 24 contribuciones y su base; las barras y
la comparación verifican sus anchuras contra los pesos originales. El beeswarm
usa esa misma matriz y los valores reales de las features. Las tablas de este
informe se generan en la misma ejecución. El redondeo visual no se utiliza
para comprobar aditividad.

## Limitaciones

- SHAP explica el comportamiento del modelo; no demuestra causalidad ni
  justifica decisiones sanitarias por sí solo.
- Los pesos no son porcentajes, cantidades de casos o probabilidades de brote.
  La etiqueta es presencia de al menos un caso de dengue, no brote ni malaria.
- Los modelos finales se ajustaron sobre todas las filas elegibles del panel.
  Esta demostración **no constituye validación predictiva fuera de muestra**,
  ni reproduce los modelos históricos de cada origen walk-forward.
- El panel original contiene solo 13 semanas de 2026. No demuestra
  generalización entre años, estaciones o territorios no representados.
- Los rezagos y las medias móviles están correlacionados: la atribución depende
  del modelo y del método de referencia. No debe leerse como un efecto aislado.
- El resumen excluye filas incompletas por claridad visual. No se imputaron
  datos; el modelo y TASK-013 admiten NaN, pero aquí se analiza otro subconjunto.
- Las probabilidades mostradas son salidas del modelo, no garantías calibradas
  de ocurrencia ni niveles de riesgo operativos.

## Reproducción

Desde la raíz del repositorio en PowerShell:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$documento = Get-Content -Raw -Encoding UTF8 docs/evidencias/reproducir_shap.md
$codigo = [regex]::Match($documento, '(?s)```python\r?\n(.*)\r?\n```\s*$').Groups[1].Value
$codigo | ./.venv/Scripts/python.exe -B -
```

El generador completo está en [reproducir_shap.md](reproducir_shap.md).
No instala dependencias. Se fija la semilla solo para la distribución visual
de puntos del beeswarm, sin alterar datos, modelos o pesos.

## Entorno de generación

- Python: 3.12.10
- shap: 0.52.0
- xgboost: 2.1.1
- matplotlib: 3.11.2
- pandas: 2.2.3
- numpy: 2.5.3

## Trazabilidad SHA-256 de fuentes

- `data\processed\panel_semanal_dengue_clima.csv`: `2df02d3934f72e92b07864fb8947652e86c321218938112d5f3f7921ba7c699f`
- `dengue-malaria-prediccion\app\ml\features.py`: `f63ee39108b5d89a8d7d681eb0e63564d48d0cb070b2f5fc4a88921e0e84aefb`
- `dengue-malaria-prediccion\app\ml\entrenamiento.py`: `ad4541276109dd5e95b696bc74d9c0465c7484f87bfd036714bddb809f6b67db`
- `dengue-malaria-prediccion\app\ml\explicabilidad.py`: `d20191d0d1c176d13f2218ada5aab46d16882672fb84a7bcf4299cf9039e1552`
- `dengue-malaria-prediccion\app\ml\artifacts\baseline_dengue_t3_v1.json`: `9158b427d98c7b14fde97895bfbfb77dd666b4d43b13648ad8ea680962f88234`
- `dengue-malaria-prediccion\app\ml\artifacts\baseline_dengue_t3_v1_metadata.json`: `4cee885021fad6ce25c97d112e5da7ea2befc1b0e8320176c737e1b79eed9adb`
- `dengue-malaria-prediccion\app\ml\artifacts\baseline_dengue_t4_v1.json`: `ed1c4743342250786428c2da28fa19467bc573afe0031ba0bae17a8f06d992c4`
- `dengue-malaria-prediccion\app\ml\artifacts\baseline_dengue_t4_v1_metadata.json`: `9bc40b5399b62611b1045b8dc87a8b155bfa9008fde917df72237bf4cef8e69a`

## Archivos para guardar en Git

- Este informe y `docs/evidencias/reproducir_shap.md`.
- Los siete PNG de `docs/evidencias/shap/`. No requieren DVC.
