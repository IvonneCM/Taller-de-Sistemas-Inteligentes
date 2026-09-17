# Métricas de valor y criterios de éxito

**Responsable:** Tania Perez
**Sección del backlog:** Discovery
**Trazabilidad:** NFR-001, NFR-002, NFR-007, `docs/product_goal.md`

---

## 1. Por qué se separan dos conjuntos de métricas

Esta entrega **no incluye un modelo de predicción entrenado** (ver
`dengue-malaria-prediccion/tasks.md`, Fase 3 en adelante, aún no iniciada).
Por eso no tiene sentido medir todavía precisión de predicción. Lo que sí
puede y debe medirse en esta etapa es si los **datos y el pipeline** están
en condiciones de sostener esas métricas cuando exista un modelo.

Este documento separa explícitamente:

1. Métricas del **sistema final** (NFR-001, NFR-002): objetivos de diseño,
   todavía no validados con resultados.
2. Métricas de **esta entrega**: evidencia real, medida hoy, sobre calidad
   y cobertura de los datos disponibles.

## 2. Métricas del sistema final

| Métrica | Definición (requirements.md) | Cómo se medirá | Con qué datos |
|---|---|---|---|
| **NFR-001 — Precisión espacial** | El modelo deberá alcanzar una precisión espacial mínima del **75%** en la zona piloto. | Comparar, por municipio y semana, si la clasificación de riesgo del modelo (alto/medio/bajo) coincide con la ocurrencia real de un aumento de casos confirmado a posteriori. Se calculará como % de municipios-semana correctamente clasificados sobre el total evaluado. | Serie municipio-semana de dengue/malaria (aún no disponible; ver §4) cruzada con las predicciones generadas por el motor de predicción (Fase 3 de `tasks.md`, no iniciada). |
| **NFR-002 — Anticipación mínima** | El sistema deberá anticipar brotes al menos **2 semanas** antes de su confirmación clínica. | Medir la diferencia, en semanas epidemiológicas, entre la fecha en que el modelo emite una alerta y la fecha en que el reporte oficial confirma el aumento de casos en esa zona. | Igual que NFR-001: requiere la serie semanal municipal que hoy no existe (ver limitación en `docs/eda_inicial.md` §16). |
| **NFR-007 — Tolerancia a datos incompletos** | El pipeline debe seguir operando (con confianza reducida) con hasta 20% de registros climáticos ausentes en una ventana. | % de municipio-semana que caen en cada nivel de confianza (`confianza_normal` ≤5% faltante, `confianza_baja` 5-20%, `datos_insuficientes` >20%). | Datos climáticos procesados (`data/processed/clima_semanal.csv` y su continuación con imputación, ver nota en §5). |

### Inconsistencia detectada y corregida

`docs/product_goal.md` decía *"≥80% precisión"* y *"lead time 3-4 semanas
mínimo"*, mientras que `requirements.md` fija NFR-001 en **75%** y NFR-002
en **al menos 2 semanas** (con 3-4 semanas como objetivo de diseño, no como
mínimo). Ambas cifras ya se corrigieron en `product_goal.md` para citar
directamente NFR-001/NFR-002 en vez de repetir números sueltos — así solo
hay una fuente de verdad (`requirements.md`) para estas dos métricas.

## 3. Métricas de esta entrega (evidencia real, ya medida)

Estas métricas no predicen brotes: miden si la **base de datos** sobre la
que se construirá el modelo es utilizable. Toman los números ya publicados
y reproducibles en `docs/eda_inicial.md`.

| Métrica de esta entrega | Valor medido | Fuente |
|---|---|---:|
| Registros climáticos RAW obtenidos (SENAMHI) | 16.778 | `docs/eda_inicial.md` §4 |
| Registros descartados por control de calidad | 24 (0.14%) | `docs/eda_inicial.md` §4 |
| Municipios con cruce real clima + dengue | 4 de 4 climáticos | `docs/eda_inicial.md` §10 |
| Municipios con cruce real clima + malaria | 3 de 4 climáticos | `docs/eda_inicial.md` §10 |
| Cobertura climática semanal suficiente — Guayaramerín | 100.00% | `docs/eda_inicial.md` §6 |
| Cobertura climática semanal suficiente — Ixiamas | 100.00% | `docs/eda_inicial.md` §6 |
| Cobertura climática semanal suficiente — Palos Blancos | 54.55% | `docs/eda_inicial.md` §6 |
| Cobertura climática semanal suficiente — San Buenaventura | 27.27% | `docs/eda_inicial.md` §6 |

Estas dos últimas filas (Palos Blancos y San Buenaventura) son precisamente
la evidencia que justifica NFR-007 y el trabajo de imputación definido en
`docs/reglas_calidad_datos.md` — son **datos reales, no supuestos**, de que
la cobertura irregular es un riesgo concreto y no hipotético.

## 4. Qué falta para poder medir NFR-001/NFR-002 con datos reales

Ambas métricas del sistema final dependen de una serie **municipio-semana**
de casos de dengue/malaria. Hoy solo existen acumulados municipales
SE1-SE13 (ver `docs/eda_inicial.md` §16, "Limitación temporal"). Mientras
esa limitación no se resuelva con el SEDES/Ministerio de Salud, NFR-001 y
NFR-002 permanecen como objetivos de diseño, no como resultados medibles —
consistente con la Regla de Evidencia de la guía de defensa: se documenta
la justificación técnica de cómo se medirán, no se deja en blanco ni se
inventa un resultado.

## 5. Nota sobre el pipeline de limpieza

El trabajo de imputación climática (que mejora directamente los porcentajes
de cobertura de la tabla del §3) ya está construido, probado y subido al
repositorio (`scripts/limpieza_datos.py`, `docs/pipeline_datos.md`). Con
los datos imputados, 43 de las 44 filas municipio-semana quedan en
`confianza_normal` y ninguna en `datos_insuficientes` — una mejora medible
frente a la cobertura cruda de la tabla anterior. Ese resultado no se
incorpora a la tabla del §3 porque esta sección documenta específicamente
la evidencia **sin imputar** que justifica por qué la imputación era
necesaria; el detalle completo está en `docs/pipeline_datos.md` §3.
