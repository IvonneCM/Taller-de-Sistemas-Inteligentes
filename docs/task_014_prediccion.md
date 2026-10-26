# TASK-014: pipeline de predicción semanal (features → modelo → SHAP)

Implementación: `dengue-malaria-prediccion/app/ml/prediccion.py`.
ORM: `dengue-malaria-prediccion/app/models/prediccion.py` (tabla
`predicciones`).
Migración: `alembic/versions/5f6a7b8c9d01_task_014_predicciones.py`.
Pruebas: `dengue-malaria-prediccion/tests/ml/test_prediccion.py`.

No reentrena el modelo. Reutiliza los artefactos de TASK-012
(`app/ml/artifacts/`) y las features de TASK-011; llama a SHAP de TASK-013
para llenar `variables_explicativas`.

## Decisiones de alcance

### 1. Horizontes: t+3 operativo, t+4 disponible pero no publicado

El lote semanal publica **solo t+3** por defecto:

- REQ-002 exige un horizonte de 3 a 4 semanas; 21 días cumple ese rango.
- El walk-forward de t+4 tiene solo **2 orígenes** (56 predicciones) frente a
  4 orígenes de t+3. La validación a cuatro semanas es más débil, tal como
  ya advierte `docs/task_012_baseline.md`.
- La tabla `predicciones` de `design.md` §3 **no tiene columna de horizonte**.
  Publicar t+3 y t+4 en la misma fecha crearía dos filas por municipio que el
  consumidor no puede distinguir salvo por `fecha_estimada_riesgo`, y TASK-015
  podría generar dos alertas para el mismo riesgo.

`generar_predicciones(..., horizonte=4)` funciona y usa el artefacto t+4.
Si el equipo decide publicar ambos horizontes, primero debe agregarse
`horizonte_semanas` (o una regla de selección única) al esquema y a los
endpoints; no se hizo en TASK-014 para no inventar requisitos.

### 2. `nivel_riesgo`: cortes provisionales, no validados

No existen cortes definidos en `requirements.md` ni en `design.md`. Se usan:

| Probabilidad | Nivel |
|---|---|
| `< 33.33 %` | bajo |
| `>= 33.33 %` y `< 66.67 %` | medio |
| `>= 66.67 %` | alto |

Estos cortes **no son una definición de brote ni están validados
empíricamente**. Son configurables en el módulo y deben revisarse cuando
exista una serie histórica más larga. El umbral de alerta de REQ-009 es un
concepto distinto y se configura en `umbrales_configuracion` (TASK-015/023).

### 3. `nivel_confianza`: NFR-007 estricto

Se reutilizan los umbrales de `app/etl/limpieza.py` (TASK-010):

| Faltantes/imputados en la ventana | `nivel_confianza` | ¿Se publica? |
|---|---|---|
| `<= 5 %` | `alto` | Sí |
| `> 5 %` y `<= 20 %` | `bajo` | Sí |
| `> 20 %` | — | **No** (`datos_insuficientes`) |

`medio` queda reservado y esta versión no lo emite. El porcentaje debe venir
de TASK-010 o de `clima_semanal_calidad.csv`. Si el llamador no lo entrega,
el módulo estima la proporción de **features climáticas ausentes** en la
ventana; esa estimación no detecta valores ya imputados, porque el panel v2
de NASA POWER no conserva `es_dato_imputado`.

### 4. Alcance de datos: 28 se puntúan, 4 se persisten

El artefacto de TASK-012 fue entrenado con el panel de **28 municipios**.
TASK-014 genera predicciones para los 28 en memoria, pero
`persistir_predicciones` solo inserta los municipios que existen en el
catálogo actual (`app/etl/seed_catalogo.py`): Guayaramerín, Ixiamas, Palos
Blancos y San Buenaventura.

Ampliar el catálogo a 28 no corresponde a TASK-014: requiere geometrías
oficiales en `municipios` (NOT NULL, PostGIS) y es parte de la capa de datos
de Tania (TASK-005/seed). Hasta entonces, las 24 filas restantes se reportan
como `municipio_no_en_catalogo`, no se descartan silenciosamente.

## Uso

Desde `dengue-malaria-prediccion/`:

```python
from datetime import datetime, timezone
from app.ml.features import cargar_features
from app.ml.prediccion import generar_predicciones

resultado = cargar_features()
predicciones = generar_predicciones(
    resultado,
    horizonte=3,
    fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
)
```

Cada `PrediccionCalculada` incluye:

- `municipio`, `enfermedad`, `horizonte_semanas`;
- `fecha_generacion` y `fecha_estimada_riesgo` (+21 o +28 días);
- `probabilidad_pct`, `nivel_riesgo`, `nivel_confianza`;
- `variables_explicativas`: ranking SHAP local en **log-odds**;
- `publicada` y `motivo_no_publicacion` (`sin_features` o
  `datos_insuficientes`).

Para persistir (requiere `DATABASE_URL` y un `modelo_id` existente):

```python
from app.ml.prediccion import persistir_predicciones

resumen = persistir_predicciones(predicciones, modelo_id=1)
```

`persistir_predicciones` solo hace `INSERT`, nunca `UPDATE` (NFR-009).
También valida el horizonte de 21 a 28 días y que una predicción publicada
tenga al menos una variable explicativa.

CLI:

```powershell
python -m app.ml.prediccion --horizonte 3 --modelo-id 1
python -m app.ml.prediccion --horizonte 3 --fecha-generacion 2026-03-30 --porcentaje-faltante 10
```

Sin `--modelo-id` el comando es una simulación: calcula y muestra el resumen,
pero no escribe en la base de datos.

## Entrenamiento y división cronológica

TASK-014 **no entrena**. La división cronológica ya está en
`app/ml/entrenamiento.py` (`particiones_walk_forward`): el entrenamiento de
cada origen solo usa filas cuyo objetivo estaría disponible antes del origen;
nunca hay división aleatoria ni filas de Caranavi mezcladas con el futuro de
otros municipios. TASK-014 solo consume el artefacto final ya entrenado.

## Verificación

- `python -m unittest discover -s tests/ml -p "test_prediccion.py" -v`:
  **18 pruebas OK** (incluye integración con los artefactos reales y SHAP
  cuando está instalado).
- Migración aplicada sobre PostgreSQL 16 + PostGIS temporal:
  `alembic upgrade head` y `alembic check` sin operaciones nuevas.
- Inserción real en una transacción: **28 predicciones generadas, 4
  insertadas (piloto), 24 omitidas por catálogo**, todas con 24 variables
  SHAP. La transacción se revirtió; no quedaron datos de prueba.
- `ruff check` sobre los archivos nuevos: sin errores.
- `python -m compileall -q app tests`: OK.

## Limitaciones

- El modelo es un baseline exploratorio; sus probabilidades no están
  calibradas. Los cortes de riesgo son provisionales.
- La etiqueta es “al menos un caso”, no una definición de brote.
- El panel cubre SE1-SE13 de 2026; no hay ciclo anual ni validación entre
  años.
- El clima de NASA POWER es modelado, no observado.
- La confianza depende de la calidad de la marca de imputación que entregue
  TASK-010; el panel actual no la conserva.
- No se publica t+4 en el lote semanal por la limitación de validación y la
  falta de columna de horizonte en `predicciones`.
- Los pesos SHAP describen el modelo, no causalidad.
