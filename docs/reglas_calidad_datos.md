# Reglas de calidad, limpieza e imputación de datos

**Autor:** Dilan Mamani

**Estado:** Propuesta para revisión del equipo

**Trazabilidad:** REQ-013, REQ-014, REQ-015, NFR-007 y TASK-010

## 1. Objetivo y alcance

Estas reglas definen cómo validar, limpiar e imputar los datos climáticos y
epidemiológicos antes de usarlos para entrenamiento o predicción. Se aplican
por municipio, enfermedad y periodo temporal, y buscan que cada transformación
sea reproducible y auditable.

Las reglas deberán implementarse en `app/etl/limpieza.py` durante TASK-010.
Hasta entonces constituyen el contrato de calidad del pipeline, no una
funcionalidad ya implementada.

## 2. Principios

1. Conservar el dato recibido y registrar por separado toda corrección.
2. No interpretar un dato ausente como cero.
3. No imputar silenciosamente: toda imputación debe quedar marcada.
4. No mezclar fuentes o unidades sin normalización explícita.
5. Separar datos provisionales de datos consolidados.
6. Detener o degradar una salida cuando la calidad no permita defenderla.

## 3. Campos mínimos de trazabilidad

Cada lote de ingesta deberá registrar como mínimo:

| Campo | Regla |
|---|---|
| `fuente` | Nombre de la institución, API o archivo de origen. Obligatorio. |
| `fecha_ingesta` | Fecha y hora UTC en la que el sistema recibió el dato. |
| `periodo_dato` | Día o semana epidemiológica a la que corresponde el valor. |
| `version_lote` | Identificador reproducible del archivo o ejecución de ingesta. |
| `estado_calidad` | `valido`, `corregido`, `imputado`, `provisional` o `rechazado`. |
| `regla_aplicada` | Código de la regla que modificó o rechazó el registro. |
| `valor_original` | Valor recibido antes de una corrección o imputación. |
| `es_dato_imputado` | `true` solo cuando el valor fue calculado, no observado. |

Los campos aún ausentes del modelo físico deberán incorporarse al diseñar las
migraciones de TASK-006. Mientras tanto, el log de calidad deberá conservar
esa información por lote.

## 4. Validaciones comunes

| Código | Validación | Acción |
|---|---|---|
| COM-01 | Municipio no existe en el catálogo oficial o está vacío. | Rechazar y enviar a revisión. |
| COM-02 | Fecha inválida, futura o fuera del periodo declarado. | Rechazar. |
| COM-03 | Fuente vacía. | Rechazar, porque incumple REQ-015. |
| COM-04 | Duplicado exacto dentro del mismo lote. | Conservar una fila y registrar el duplicado. |
| COM-05 | Mismo municipio, periodo y variable con valores distintos. | No sobrescribir; conservar versiones y priorizar la fuente oficial más reciente. |
| COM-06 | Unidad diferente de la unidad canónica. | Convertir con una regla documentada o rechazar si no es posible. |

La clave temporal esperada para clima es municipio y fecha. Para epidemiología
es municipio, enfermedad y semana epidemiológica, aunque la fuente entregue
registros diarios.

## 5. Datos climáticos

### 5.1 Unidades y rangos

| Variable | Unidad canónica | Validación automática |
|---|---|---|
| Temperatura media | grados Celsius | Valor entre -30 y 50. Fuera del rango: rechazado. |
| Humedad relativa | porcentaje | Valor entre 0 y 100. Fuera del rango: rechazado. |
| Precipitación | milímetros por día | Valor mayor o igual a 0. Negativos: rechazados. |

Los valores dentro del rango físico pero atípicos para el municipio se marcan
para revisión usando el rango intercuartílico o percentiles históricos. Un
atípico plausible no se elimina ni se reemplaza automáticamente, porque puede
representar un evento climático real.

### 5.2 Faltantes e imputación

El porcentaje de faltantes se calcula para cada variable, municipio y ventana
usada por el modelo:

```text
porcentaje_faltante = valores_ausentes / valores_esperados * 100
```

Orden de imputación:

1. Interpolación temporal lineal cuando existen observaciones válidas antes y
   después del hueco y este no supera dos periodos consecutivos.
2. Mediana histórica del mismo municipio y semana o mes del año cuando no se
   puede interpolar.
3. Mediana de municipios vecinos con fuente y periodo compatibles, solo si la
   geometría y cobertura necesarias están disponibles.
4. Si ninguna regla es aplicable, conservar el valor como ausente.

Todo valor calculado debe guardar `es_dato_imputado = true`, método, valor
original y versión del lote. Una observación real que llegue después reemplaza
el valor para ejecuciones futuras, sin borrar el historial de la imputación.

### 5.3 Umbrales de operación

| Faltantes climáticos en la ventana | Tratamiento |
|---|---|
| 0% a 5% | Imputar cuando corresponda y registrar el porcentaje. |
| Más de 5% y hasta 20% | Imputar, continuar y marcar la predicción con confianza baja. |
| Más de 20% | No publicar una predicción operativa; registrar `datos_insuficientes` y solicitar revisión. |

El tramo de hasta 20% satisface la tolerancia mínima definida por NFR-007. El
sistema no promete una predicción defendible por encima de ese umbral.

## 6. Datos epidemiológicos

### 6.1 Validaciones

| Código | Validación | Acción |
|---|---|---|
| EPI-01 | Casos confirmados no enteros o negativos. | Rechazar. |
| EPI-02 | Enfermedad distinta de dengue o malaria en el alcance inicial. | Separar del conjunto del MVP. |
| EPI-03 | Semana epidemiológica inválida. | Rechazar. |
| EPI-04 | Salto atípico respecto al historial. | Marcar para revisión; no eliminar automáticamente. |
| EPI-05 | Registro individual o con identificadores personales. | Rechazar y no persistir, conforme a REQ-020. |

Los conteos se agregan por municipio, enfermedad y semana epidemiológica. No
se almacenan nombre, documento de identidad, dirección, historia clínica ni
coordenadas de pacientes.

### 6.2 Faltantes y retraso de reporte

Un reporte ausente no equivale a cero casos. Se aplican estas reglas:

1. Si no llegó el reporte de una semana, marcarla `pendiente_reporte`; no
   imputar un conteo de casos para presentación operativa.
2. Si la fuente declara cero casos, conservar cero como valor observado y
   diferenciarlo de un faltante.
3. Mantener fecha del periodo epidemiológico y fecha de recepción para medir
   el retraso.
4. Considerar provisionales las semanas recientes dentro de la ventana de
   retraso acordada con la fuente.
5. Cuando llegue una actualización tardía, crear una nueva versión del lote y
   recalcular los agregados y predicciones afectadas; no borrar la versión
   usada originalmente.
6. Excluir de entrenamiento las semanas pendientes o provisionales cuando no
   exista una estrategia de corrección de retraso validada por el equipo.

La ventana exacta para considerar un reporte consolidado deberá definirse con
SEDES o con la fuente epidemiológica seleccionada antes de TASK-009.

## 7. Salida del control de calidad

Cada ejecución debe producir un resumen por lote con:

- cantidad recibida, válida, corregida, imputada, provisional y rechazada;
- porcentaje de faltantes por variable y municipio;
- duplicados y conflictos encontrados;
- reglas aplicadas y motivos de rechazo;
- fuente, versión y fecha de ejecución;
- municipios sin calidad suficiente para generar una predicción.

El pipeline no debe continuar si falta la fuente, no puede identificarse el
municipio o se detectan datos personales. Los demás problemas deben quedar
visibles en el log y reflejarse en el nivel de confianza.

## 8. Criterios de aceptación

La implementación de TASK-010 se considerará conforme cuando existan pruebas
automatizadas que demuestren:

1. rechazo de fechas, unidades y rangos inválidos;
2. deduplicación sin pérdida del valor original;
3. imputación climática reproducible y marcada;
4. confianza baja entre más de 5% y 20% de faltantes;
5. bloqueo de la predicción por encima del 20%;
6. distinción entre cero casos y reporte ausente;
7. conservación de versiones ante reportes epidemiológicos tardíos;
8. ausencia de datos personales en las salidas y logs.

## 9. Revisión pendiente

Antes de aprobar estas reglas, el equipo debe confirmar la fuente climática,
la fuente epidemiológica, la granularidad real de sus datos y la ventana de
consolidación de reportes. La revisión debe quedar registrada en el acta o en
la herramienta de gestión del proyecto.
