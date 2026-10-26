# TASK-011: variables semanales para GatoByte

Implementación: `dengue-malaria-prediccion/app/ml/features.py`.
No escribe archivos, modifica datasets ni consulta la base de datos.
Solo necesita pandas y la biblioteca estándar de Python.

## Uso

Desde `dengue-malaria-prediccion/`:

```python
from app.ml.features import cargar_features, generar_features

resultado = cargar_features()  # panel_semanal_dengue_clima.csv de la raíz
X = resultado.features        # solo predictores numéricos
y = resultado.objetivos       # objetivos existentes; nunca entran en X
claves = resultado.claves     # municipio, enfermedad, año, semana y lunes ISO
historia = resultado.continuidad  # presencia de las cuatro semanas previas

# También admite un DataFrame semanal preparado por el consumidor:
# resultado = generar_features(datos)
```

Las cuatro salidas tienen el mismo índice, ordenado por municipio,
enfermedad y fecha. No se eliminan filas por falta de historia: los valores
desconocidos permanecen como NaN. El consumidor debe seleccionar las filas
con features y objetivo disponibles; no debe convertir faltantes en ceros.
Las claves y la marca de continuidad son metadatos separados de `X`.

Ejemplo de preparación para el modelo de Ivonne (sin entrenarlo):

```python
objetivo = resultado.objetivos["casos_dengue_t_mas_3"]
utiles = resultado.features.notna().all(axis=1) & objetivo.notna()
X = resultado.features.loc[utiles]
y = objetivo.loc[utiles]
# X e y están alineados. Separar cronológicamente antes de model.fit().
# Si el estimador requiere un array: X.to_numpy(dtype=float).
```

Con el panel actual y las ventanas completas del modo predeterminado,
quedan 168 filas con objetivo t+3 y 140 con objetivo t+4 (24 features).
La entrada vacía se rechaza con ValueError para evitar devolver un esquema
sin columnas al consumidor.

## Variables y ventanas

Reconoce las columnas reales `casos_dengue`, `temperatura_media`,
`humedad_media` y `precipitacion_total_mm`. También admite
`casos_confirmados` para una tabla semanal con enfermedad explícita.
Solo procesa las variables presentes. Si falta `enfermedad`, únicamente
infiere `dengue` cuando existe `casos_dengue`.

Para cada variable `v`, genera:

- `v_lag2`, `v_lag3`, `v_lag4`: valores exactamente 14, 21 y 28 días atrás.
- `v_media_movil_2sem`, `v_media_movil_3sem`, `v_media_movil_4sem`:
  promedio de las 2, 3 o 4 semanas anteriores, excluyendo la actual.

El criterio proviene de `scripts/construir_panel_semanal.py`, sin importar
ni ejecutar su pipeline. Se sustituyen los desplazamientos por posición
por consultas de fecha exacta dentro de cada municipio y enfermedad.
Las medias requieren todas las semanas y valores de la ventana. No se
rellenan huecos ni se incorporan registros nuevos a la salida.

Se rechazan claves duplicadas, identificadores vacíos, semanas ISO
inválidas, valores no numéricos y valores infinitos. Las columnas de
rezagos precalculados del panel se ignoran y se recalculan desde las
variables originales; no se arrastran columnas arbitrarias a los predictores.

## Disponibilidad temporal y objetivos

Por defecto, ni los valores actuales ni los objetivos futuros aparecen en
`features`. `objetivos` conserva, cuando existen, `casos_dengue_t_mas_3`,
`casos_dengue_t_mas_4` y `hay_casos_t_mas_3`. No genera objetivos nuevos.

`incluir_semana_actual=True` incorpora los valores actuales como features
y cambia las medias a ventanas terminadas en esa semana (por ejemplo,
media de 2 semanas = t-1 y t). Los rezagos siguen siendo t-2, t-3 y t-4.
Esta opción solo corresponde a una predicción al cierre de la semana,
cuando sus datos ya están disponibles; nunca a una predicción previa.

El módulo no conoce la fecha real de publicación de cada observación.
Los casos corregidos retrospectivamente y el clima de reanálisis pueden
no haber estado disponibles al emitir una predicción histórica. Una
evaluación operativa requiere versiones de datos conocidas en cada fecha,
particiones temporales y que los objetivos de entrenamiento hayan sido
observados antes del corte de validación.

## Limitaciones

- Dengue disponible: 28 municipios, 13 semanas de 2026. Al calcular desde
  este panel, no existe historia previa a SE1 para casos ni clima. Por ello
  los rezagos climáticos iniciales quedan NaN aunque el panel original
  incluya rezagos precalculados con historia NASA de 2025. Para aprovechar
  esa historia, el consumidor puede proporcionar una tabla semanal más
  extensa con el mismo esquema; este módulo no cambia la ingesta.
- Las semanas se interpretan como ISO, tal como el pipeline climático
  existente. Debe validarse su alineación con el calendario epidemiológico
  de la fuente antes del uso operativo.
- Malaria disponible por bloques de longitud variable no permite lags
  semanales de casos. Las entradas con `se_inicio`, `se_fin` o `n_semanas`
  se rechazan: no se distribuyen acumulados entre semanas. Una serie
  semanal auténtica con enfermedad explícita sí puede procesarse.
- La integración con tablas del backend requiere ingesta semanal real;
  el conector epidemiológico actual sigue ingiriendo acumulados. No se
  modificó ese conector ni el catálogo de municipios.
- No se define un umbral de brote, entrena un modelo ni calcula métricas
  predictivas. `hay_casos_t_mas_3` no equivale a una etiqueta de brote.

## Pruebas sin instalación ni base de datos

Desde `dengue-malaria-prediccion/`, con el entorno existente de la raíz:

```powershell
../.venv/Scripts/python.exe -B -m unittest discover -s tests/ml -p 'test_*.py' -v
```

Las pruebas también son compatibles con pytest. Se usa unittest para
ejecutarlas de forma aislada porque pytest no está instalado en el entorno
actual y el `tests/conftest.py` compartido importa configuración de BD.

## Entrega a Ivonne: importación y partición temporal reproducible

Este ejemplo puede ejecutarse desde una consola Python en la raíz o en el
backend. Para incorporarlo posteriormente a un script ubicado en `scripts/`,
la rama de `__file__` resuelve la raíz independientemente del directorio de
ejecución. No requiere cambiar el entrenamiento actual ni instalar el backend
como paquete. `cargar_features()` también admite una ruta explícita al CSV.

`X` sale exclusivamente de `resultado.features`; `y` es una sola columna de
`resultado.objetivos`. `fecha_semana` sale de `resultado.claves` y nunca se
concatena a los predictores. Todos se seleccionan con las mismas máscaras.
Las filas están ordenadas por municipio: no usar posiciones para dividirlas.

Convención del ejemplo: se predice al inicio de la semana t usando solo
semanas anteriores. El objetivo de la semana t+h se considera disponible
al inicio de t+h+1, más `retraso_semanas` adicionales. Es una hipótesis de
evaluación, no una fecha de publicación confirmada. El entrenamiento exige
`fecha_disponible <= corte`; la validación usa `fecha_semana >= corte`.
Las filas antiguas con objetivo aún no disponible quedan en `excluido`,
no se trasladan a validación. Todos los municipios de una fecha tienen el
mismo lado temporal antes de filtrar por disponibilidad de datos.

```python
# EJEMPLO_REPRODUCIBLE_TASK_011
from pathlib import Path
import sys
import pandas as pd

if "__file__" in globals():  # script ubicado en scripts/
    RAIZ = Path(__file__).resolve().parents[1]
else:  # consola o notebook en raíz o backend
    RAIZ = Path.cwd()
    if RAIZ.name == "dengue-malaria-prediccion":
        RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ / "dengue-malaria-prediccion"))

from app.ml.features import cargar_features


def preparar_particion(resultado, horizonte, corte, *,
                       exigir_historia_completa=True, retraso_semanas=0):
    if horizonte not in (3, 4):
        raise ValueError("El horizonte debe ser 3 o 4.")
    if not isinstance(retraso_semanas, int) or retraso_semanas < 0:
        raise ValueError("retraso_semanas debe ser un entero no negativo.")
    corte = pd.Timestamp(corte)
    fechas = resultado.claves["fecha_semana"]
    objetivo = resultado.objetivos[f"casos_dengue_t_mas_{horizonte}"]
    disponibles = fechas + pd.Timedelta(weeks=horizonte + 1 + retraso_semanas)
    conocidas = resultado.features.notna()
    historia = (conocidas.all(axis=1) if exigir_historia_completa
                else conocidas.any(axis=1))
    elegibles = historia & objetivo.notna()
    entrenamiento = elegibles & fechas.lt(corte) & disponibles.le(corte)
    validacion = elegibles & fechas.ge(corte)
    excluido = ~(entrenamiento | validacion)
    salida = {"mascaras": {"train": entrenamiento, "test": validacion,
                            "excluido": excluido},
              "fecha_disponible": disponibles}
    for nombre, mascara in (("train", entrenamiento), ("test", validacion)):
        salida[nombre] = {
            "X": resultado.features.loc[mascara],
            "y": objetivo.loc[mascara],
            "fecha_semana": fechas.loc[mascara],
        }
    return salida


resultado = cargar_features(
    RAIZ / "data/processed/panel_semanal_dengue_clima.csv",
    incluir_semana_actual=False,
)
particiones = {}
for horizonte in (3, 4):
    particiones[horizonte] = preparar_particion(
        resultado, horizonte, "2026-02-23",  # inicio ISO-SE9
        exigir_historia_completa=(horizonte == 3),
    )
    p = particiones[horizonte]
    print(f"t+{horizonte}: train={p['train']['X'].shape}, test={p['test']['X'].shape}")
    assert p["train"]["X"].index.equals(p["train"]["y"].index)
    assert p["test"]["X"].index.equals(p["test"]["y"].index)
    # Posteriormente: modelo.fit(p['train']['X'], p['train']['y'])
```

`preparar_particion()` es una función del ejemplo documentado, no una nueva
función de `app.ml.features`. Las pruebas ejecutan este mismo bloque para
comprobar que el ejemplo sea reproducible y que las máscaras respeten el corte.

Con el CSV actual y el corte indicado:

| Horizonte | Política de NaN | Entrenamiento | Validación |
|---|---|---:|---:|
| t+3 | Todas las features disponibles | 28 | 56 |
| t+4 | Conservar NaN; excluir filas con todas las features ausentes | 56 | 28 |

En t+4, exigir historia completa con ese corte produce **0 filas de
entrenamiento**. Con 13 semanas no existe un corte con ambos conjuntos no
vacíos y esa política estricta: la primera fila con historia completa es
SE5, cuyo objetivo SE9 se conoce, bajo la hipótesis, recién al inicio de
SE10; desde SE10 ya no hay objetivos t+4 observados en este CSV.

La alternativa de t+4 conserva NaN para un estimador que admita faltantes,
como XGBoost; no equivale a tener historia completa. No rellenar con cero
ni interpolar usando semanas futuras. Para otros estimadores, cualquier
imputador debe ajustarse exclusivamente en entrenamiento. Los objetivos
NaN siempre se excluyen. La validación representa predicciones sucesivas
en cada fecha t; no un pronóstico de todas las fechas emitido de una vez
en el corte. Su tamaño no permite conclusiones de desempeño operativo.

## Validaciones de entorno pendientes

El módulo solo importa pandas; XGBoost/scikit-learn están declarados en
`dengue-malaria-prediccion/requirements.txt`, pero no son necesarios para
calcular features. La prueba opcional de integración construye DMatrix,
entrena un booster mínimo en memoria y predice para ambos horizontes,
sin guardar modelos ni tocar el entrenamiento de Ivonne. Se omite con una
razón explícita si XGBoost no está instalado; errores de una instalación
presente se consideran fallos, no se ocultan como omisiones.

Se revisaron el Python de `.venv` (pandas 3.0.5) y el Python global
(pandas 3.0.3): ninguno tiene XGBoost ni pandas 2.2.3. La ejecución con
**pandas 2.2.3 permanece pendiente**; la inspección de APIs no sustituye
esa prueba. No se modificaron requirements ni se instalaron dependencias.
Cuando exista un entorno autorizado con pandas 2.2.3, ejecutar allí el
mismo comando de unittest usando su intérprete: toda la suite, incluida
la prueba específica de esa versión, debe pasar. No combinar los dos
requirements del repositorio, que fijan versiones diferentes de pandas.

Resultado de preparación de entrega: se ejecutaron las 22 pruebas de
`tests/ml/` con Python 3.12.10, tanto en `.venv` (pandas 3.0.5) como en
el intérprete global (pandas 3.0.3). En cada entorno: **20 aprobadas,
2 omitidas, 0 fallidas**. Las omisiones corresponden exclusivamente a
XGBoost y pandas 2.2.3 ausentes. El ejemplo de ambos horizontes se ejecuta
como parte de la suite. TASK-011 puede compartirse con estas validaciones
pendientes explícitas; no se certifica aún el entrenamiento en el entorno
de Ivonne ni la disponibilidad histórica real de las etiquetas.
