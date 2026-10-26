# TASK-013: explicabilidad local mediante SHAP

Implementación: `dengue-malaria-prediccion/app/ml/explicabilidad.py`.
Utiliza los dos Booster reales de TASK-012, cargados mediante
`cargar_artefacto(3)` y `cargar_artefacto(4)`. No reentrena ni modifica
modelos, metadatos o datos. No requiere base de datos.

## Uso

Desde `dengue-malaria-prediccion/`, con un entorno que ya disponga de las
dependencias ML declaradas en su `requirements.txt`:

```python
import json
from app.ml.features import cargar_features
from app.ml.explicabilidad import explicar_observacion, explicar_observaciones

resultado = cargar_features()
# Features exclusivamente; no pasar claves ni objetivos del panel.
X = resultado.features
fila = X.loc[X.notna().all(axis=1)].iloc[:1]
for horizonte in (3, 4):
    explicacion = explicar_observacion(fila, horizonte)
    print(json.dumps(explicacion, ensure_ascii=False, allow_nan=False, indent=2))

lote = explicar_observaciones(X.iloc[:3], 3)
```

La función individual exige un DataFrame de una fila y devuelve un diccionario.
La función plural devuelve una lista en el orden original de las filas, incluso
si el índice tiene duplicados. No incluye identificadores; el consumidor debe
mantener la asociación posicional con las claves de TASK-011.
El argumento opcional `directorio` permite indicar otra ubicación de los
artefactos v1, sin modificarla.

## Significado de la respuesta

- `horizonte_semanas`: 3 o 4.
- `valor_base`: valor esperado del margen según las rutas del modelo.
- `salida_modelo`: margen real del Booster (`output_margin=True`).
- `escala`: siempre `log_odds`, para el objetivo `binary:logistic`.
- `explicaciones`: las 24 variables, ordenadas por peso absoluto descendente;
  en empates se conserva el orden del artefacto. Los pesos son números con signo.

Un peso positivo eleva el margen respecto de la base; uno negativo lo reduce.
Los pesos no son porcentajes ni cantidades de casos. La probabilidad de al
menos un caso se obtiene aplicando la sigmoide al margen completo:
`p = 1 / (1 + exp(-salida_modelo))`. No aplicar esa transformación a cada peso.

Se configura `shap.TreeExplainer(modelo, model_output="raw",
feature_perturbation="tree_path_dependent")`, sin dataset de fondo adicional:
se usan las frecuencias de entrenamiento registradas en las rutas del árbol.
La documentación oficial describe esta escala y el método en
[TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).

Se habilita la comprobación aditiva de SHAP y se verifica además contra el
margen del Booster: `valor_base + suma(pesos) ≈ salida_modelo`, con tolerancias
absoluta y relativa de `1e-5`. Una discrepancia impide devolver la explicación.

Ejemplo JSON **solo ilustrativo del formato**, abreviado a dos variables;
no corresponde a una ejecución real. Las respuestas reales contienen 24:

```json
{
  "horizonte_semanas": 3,
  "valor_base": 0.2,
  "salida_modelo": -0.3,
  "escala": "log_odds",
  "explicaciones": [
    {"variable": "casos_dengue_lag2", "peso": -0.75},
    {"variable": "temperatura_media_lag2", "peso": 0.25}
  ]
}
```

## Validación y errores

El esquema debe coincidir exactamente con `artefacto.features`: se rechazan
columnas ausentes, adicionales, duplicadas o desordenadas. No se reordenan
silenciosamente. Se aceptan números reales y NaN, incluidos faltantes nullable
de pandas, sin imputar ni modificar la entrada. Se rechazan texto (incluso
números como texto), booleanos, complejos, infinitos, valores fuera del rango
float32 y entradas vacías o que no sean DataFrame.

Horizontes distintos de los enteros 3 y 4 producen `ValueError`.
Errores de esquema y valores producen `ValueError` o `TypeError`.
La ausencia de artefactos produce `FileNotFoundError`, y la de dependencias,
`ImportError`/`ModuleNotFoundError`. Errores de carga o de SHAP se propagan.
Formas incompatibles, resultados no finitos o no aditivos producen
`RuntimeError`. Nunca se generan explicaciones de sustitución.

## Pruebas y estado de ejecución

Desde el backend, sin generar bytecode ni ejecutar los tests de entrenamiento:

```powershell
../.venv/Scripts/python.exe -B -m unittest discover -s tests/ml -p test_explicabilidad.py -v
```

Las pruebas unitarias usan dobles explícitos para probar validación, contrato,
signos, ranking, aditividad y propagación de errores. No constituyen evidencia
de funcionamiento de SHAP con el modelo real.

Las dos pruebas de integración cargan los modelos existentes de t+3 y t+4 y
features del panel real. Comprueban filas con historia completa, parcial y
totalmente ausente, aditividad, serialización JSON y concordancia entre la
sigmoide del margen y `predecir_probabilidad()`. No entrenan ni guardan nada.
Solo se omiten por dependencias ausentes; una instalación presente pero rota,
un modelo ausente o una incompatibilidad provocan fallo visible.

Ejecución local: **16 pruebas por intérprete: 14 aprobadas, 2 omitidas,
0 fallidas**, tanto en `.venv` como en Python global. Las omitidas son
`test_modelo_real_t3` y `test_modelo_real_t4`: faltan SHAP y XGBoost en ambos
entornos, y también scikit-learn en `.venv`. No se obtuvo una explicación
real; el JSON anterior es únicamente ilustrativo.

## Limitaciones y pendientes

- Pendiente ejecutar la integración en un entorno con SHAP y XGBoost; ambos
  faltan en los intérpretes locales revisados. No se instalaron dependencias.
- Los requirements de raíz/backend y el entorno registrado de entrenamiento
  difieren. Debe verificarse la compatibilidad efectiva de versiones.
- Se explica presencia de dengue, no brote, número de casos ni malaria.
- SHAP describe el comportamiento del modelo; no demuestra causalidad ni
  fiabilidad epidemiológica. Rezagos y medias están correlacionados y pueden
  repartirse la atribución.
- Los artefactos finales incluyen todas las filas elegibles de entrenamiento.
  Explicarlos sobre el panel es descriptivo, no validación fuera de muestra.
  No representan los modelos históricos de cada origen walk-forward.
- Se conserva incluso una fila totalmente NaN porque XGBoost la admite;
  su explicación no implica que haya información suficiente para alertar.
- La integración con niveles de riesgo, persistencia y endpoints corresponde
  al pipeline posterior. Este módulo no los modifica.
