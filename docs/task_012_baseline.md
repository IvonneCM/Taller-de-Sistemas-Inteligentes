# TASK-012: baseline XGBoost de dengue (t+3 y t+4)

Implementación: `dengue-malaria-prediccion/app/ml/entrenamiento.py`.
Artefactos: `dengue-malaria-prediccion/app/ml/artifacts/`.
Métricas completas: `docs/task_012_metricas.json`.
Tabla ORM: `dengue-malaria-prediccion/app/models/modelo.py` (`modelos`).

## Alcance

Se entrenaron dos clasificadores binarios, uno por horizonte:

- t+3: predecir si habrá al menos un caso de dengue tres semanas después.
- t+4: ídem a cuatro semanas.

La etiqueta es `casos_dengue_t_mas_{3,4} > 0`. **No es una definición
epidemiológica de brote**; solo indica presencia de casos. Las métricas son
exploratorias y no validan NFR-001 ni NFR-002.

## Datos y features

- Panel: `data/processed/panel_semanal_dengue_clima.csv`.
- 364 filas: 28 municipios × 13 semanas (SE1-SE13 de 2026).
- 24 predictores generados por `app/ml/features.py` (TASK-011): rezagos
  climáticos y de casos, y medias móviles.
- No se imputan faltantes; XGBoost los maneja de forma nativa.
- Filas usadas en el modelo final: 224 para t+3 y 196 para t+4.

## Protocolo de validación

Walk-forward cronológico por fecha, sin división aleatoria. Para cada origen
`t`, el entrenamiento solo usa filas cuyo objetivo estaría disponible según la
hipótesis:

```text
fecha_semana + horizonte + 1 <= origen
```

La validación predice todas las filas del origen. Los orígenes efectivos son:

| Horizonte | Orígenes | Predicciones |
|---|---|---:|
| t+3 | 2026-02-09, 02-16, 02-23, 03-02 | 112 |
| t+4 | 2026-02-16, 02-23 | 56 |

La regla de disponibilidad es una **hipótesis de evaluación**, no una fecha
de publicación confirmada por SEDES.

## Resultados

Promedio macro por origen. El macro evita que un origen con más filas o mayor
prevalencia domine la comparación.

### t+3

| Modelo | F1 | ROC-AUC | PR-AUC | Brier | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.3322 | 0.6588 | 0.4178 | 0.2780 | 0.3060 | 0.6041 |
| Clase mayoritaria | 0.0000 | 0.5000 | 0.2678 | 0.2200 | 0.0000 | 0.0000 |
| Regla casos recientes | **0.4775** | **0.6913** | 0.3584 | 0.4018 | 0.3734 | 0.8577 |

### t+4

| Modelo | F1 | ROC-AUC | PR-AUC | Brier | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.3785 | 0.6268 | **0.3435** | 0.2533 | 0.2812 | 0.7084 |
| Clase mayoritaria | 0.3000 | 0.5000 | 0.2321 | 0.2194 | 0.2143 | 0.5000 |
| Regla casos recientes | 0.3255 | 0.6215 | 0.2509 | 0.5178 | 0.2535 | 0.8334 |

Métricas agrupadas (*pooled*) del modelo: t+3 F1 0.3590 / ROC-AUC 0.5762;
t+4 F1 0.3636 / ROC-AUC 0.5671. El promedio macro de ROC-AUC es mayor porque
cada origen se evalúa por separado; no implica buen desempeño operativo.

## Lectura de los resultados

- En t+3 el modelo **no supera** a la regla simple `casos_recientes` en F1 ni
  ROC-AUC. Sí mejora a la clase mayoritaria en F1 y ROC-AUC.
- En t+4 el modelo supera apenas a `casos_recientes` en F1 y ROC-AUC, pero
  pierde claramente en Brier y en recall. La evidencia no es concluyente.
- El Brier del modelo es mejor que el de la regla de casos recientes, lo que
  indica probabilidades menos extremas; aun así, el poder discriminativo es
  bajo (ROC-AUC cercano a 0.6).
- Con 13 semanas y 2-4 orígenes de validación, estos números no permiten
  afirmar superioridad ni generalización entre años. Deben presentarse como
  **línea base exploratoria**, no como resultado del sistema final.

## Gráficos

Generados por `scripts/graficos_task_012.py` a partir de un recálculo
walk-forward que se verifica contra la metadata versionada
(`verificacion_metadata.json`). Las predicciones individuales y las métricas
por origen quedan en `scripts/task_012_output/`.

### Métricas comparadas

Accuracy, balanced accuracy, precision, recall, F1 y ROC-AUC, promedio macro
por origen.

![Métricas comparadas](../scripts/task_012_output/metricas_comparadas.png)

### Matrices de confusión

Filas: resultado real; columnas: predicción. Permiten ver cuántos positivos
detecta el modelo y cuántos falsos positivos genera frente a los baselines.

![Matrices de confusión](../scripts/task_012_output/matrices_confusion.png)

### Curvas ROC y precision-recall

Las curvas usan todas las predicciones agrupadas (*pooled*). La línea punteada
de la curva PR es la prevalencia; cuanto más arriba, mejor.

![Curvas ROC y PR](../scripts/task_012_output/curvas_roc_pr.png)

### Desempeño por origen

Variabilidad de F1 y ROC-AUC entre orígenes walk-forward. En ROC-AUC, la línea
punteada marca 0.5 (equivalente a azar).

![Métricas por origen](../scripts/task_012_output/metricas_por_origen.png)

### Distribución de probabilidades

Probabilidad predicha separada por resultado real. Muestra cuánto se solapan
los positivos y negativos alrededor del umbral 0.5.

![Distribución de probabilidades](../scripts/task_012_output/distribucion_probabilidades.png)

### Importancia de variables

Ganancia relativa de XGBoost en el modelo final. Es una vista descriptiva del
modelo, **no sustituye SHAP** (TASK-013).

![Importancia de variables](../scripts/task_012_output/importancia_variables.png)

## Artefactos versionados

| Archivo | Contenido |
|---|---|
| `baseline_dengue_t3_v1.json` | Booster XGBoost en formato JSON nativo |
| `baseline_dengue_t3_v1_metadata.json` | Features, hiperparámetros, métricas y entorno |
| `baseline_dengue_t4_v1.json` | Booster XGBoost en formato JSON nativo |
| `baseline_dengue_t4_v1_metadata.json` | Features, hiperparámetros, métricas y entorno |

`cargar_artefacto(horizonte, version="v1")` valida el orden de features antes
de predecir. `predecir_probabilidad()` devuelve `P(>=1 caso en t+h)` usando la
API `Booster`/`DMatrix` de XGBoost (necesario por incompatibilidad de
`save_model` con scikit-learn 1.9).

## Registro en base de datos

La migración `4079b097a5a2_task_012_modelos.py` crea la tabla `modelos` con
`metricas_entrenamiento JSONB`. Se verificó sobre PostgreSQL 16 + PostGIS:

- `alembic upgrade head` aplicado.
- `alembic check`: "No new upgrade operations detected."
- Catálogo sembrado: 2 enfermedades y 4 municipios piloto.
- Dos filas registradas: ids 1 (t+3) y 2 (t+4), ambas con `TASK-012`,
  `enfermedad_id = 1` (dengue) y métricas JSONB válidas.

`alembic/env.py` ahora excluye dinámicamente las tablas de extensiones
PostGIS durante autogenerate, para evitar que futuras migraciones propongan
`DROP TABLE` sobre `tiger`, `topology` o `spatial_ref_sys`. Esa consulta
cierra su transacción implícita antes de iniciar la migración; sin ello, el
DDL se ejecutaba y se revertía al cerrar la conexión.

## Reproducción

Desde `dengue-malaria-prediccion/`:

```powershell
python -m app.ml.entrenamiento --todos --guardar
```

Con base de datos:

```powershell
$env:DATABASE_URL='postgresql://usuario:clave@host:puerto/dengue_malaria'
# En una base vacía, antes de Alembic:
#   CREATE EXTENSION IF NOT EXISTS postgis;
python -m alembic upgrade head
python -m app.etl.seed_catalogo
python -m app.ml.entrenamiento --todos --guardar --registrar-bd
```

La migración base no crea la extensión PostGIS; en una base vacía debe
crearse una vez con privilegios de superusuario. Se verificó un
`alembic upgrade head` desde cero en una base temporal con la extensión ya
creada: revisión final `4079b097a5a2`, tabla `modelos` presente y
`alembic check` sin operaciones pendientes.

Pruebas sin base de datos:

```powershell
python -m unittest discover -s tests/ml -p "test_*.py" -v
```

Gráficos y tablas de auditoría, desde la raíz del repositorio:

```powershell
python scripts/graficos_task_012.py
```

## Limitaciones

- La etiqueta “al menos un caso” no equivale a brote.
- El panel cubre solo SE1-SE13 de 2026; no hay ciclo anual ni validación
  entre años.
- Los casos históricos pueden haber sido corregidos retrospectivamente y no
  representan los datos disponibles en tiempo real.
- El clima de NASA POWER es modelado, no observado.
- La regla de disponibilidad `semana + horizonte + 1` es una hipótesis.
- El tamaño de validación (112 y 56 predicciones) es insuficiente para
  conclusiones operativas.
- El modelo y los artefactos son baseline; TASK-013/TASK-014 deben evaluar
  SHAP y el pipeline completo antes de usarlos en alertas.
