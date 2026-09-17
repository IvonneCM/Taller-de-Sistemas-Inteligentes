# Línea base y registro de experimentos (Línea Base — Paso 3)

**Responsable:** Ivonne Colque 
**Sección del backlog:** Build/QA/Deploy
**Estado:** referencia inicial nacional medida + justificación técnica (aún no existe modelo municipio-semana)
**Trazabilidad:** NFR-001, NFR-002, NFR-007; `requirements.md`, `design.md` §10
**Documentos relacionados:** [`metricas_valor.md`](./metricas_valor.md), [`pipeline_datos.md`](./pipeline_datos.md), [`eda_inicial.md`](./eda_inicial.md), [`reglas_calidad_datos.md`](./reglas_calidad_datos.md)
**Script reproducible:** [`../scripts/linea_base_modelo.py`](../scripts/linea_base_modelo.py) → salidas en `../scripts/linea_base_output/`

---

## 1. Por qué esta entrega presenta una referencia inicial y una justificación, y no un modelo entrenado

El sistema objetivo predice, por **municipio y semana epidemiológica**, el
riesgo de brote de dengue/malaria con 3-4 semanas de anticipación. Un modelo
supervisado para ese objetivo necesita una tabla con pares `X(t) → y(t+k)`:
el clima del municipio en la semana `t` y los **casos de la semana** `t+k`.

Hoy **ese insumo no existe**. Los datos reales disponibles son:

| Dataset | Unidad | Filas útiles para modelar |
|---|---|---:|
| `data/processed/clima_semanal.csv` | municipio + semana | 44 (4 municipios × SE3-13) |
| `data/processed/dengue_municipal_validado.csv` | municipio (acumulado SE1-13) | **4** (una sola observación por municipio) |
| `data/processed/malaria_municipal_validado.csv` | municipio (acumulado SE1-13) | **3** con dato |
| `data/processed/dengue_semanal_validado.csv` | **nacional** + semana | **13** (único con eje temporal) |

Consecuencia directa, ya anticipada por el EDA (`eda_inicial.md` §13 y §16):
el objetivo municipal solo tiene **una observación por municipio** (acumulado),
por lo que la tabla de modelado colapsa a **4 filas** (dengue) y **3** (malaria).
No se puede entrenar ni validar un modelo municipio-semana; y la regresión
logística para clasificar brotes tampoco, porque **no hay etiquetas** de
brote por municipio-semana.

Por la Regla de Evidencia, esta entrega **no se deja en blanco**: produce la
referencia numérica inicial donde sí es calculable (serie nacional) y registra
los experimentos, incluidos los fallidos, que justifican por qué el modelo
municipal aún no puede establecerse.

---

## 2. Datos usados y su carácter

- `dengue_semanal_validado.csv`: 13 semanas nacionales SE1-13 de 2026. La
  propia fuente declara el dato **provisional** (columna `estado_calidad`),
  por lo que la referencia que aquí se obtiene es **provisional y no
  operativa**.
- `dataset_integrado_municipal.csv`: 4 municipios con clima de periodo
  (SE3-13) y casos **acumulados** SE1-13. Se usa solo para el experimento
  cross-sectional C.
- No se generaron ni inventaron datos.

---

## 3. Baselines que la línea base deberá superar

Se definen como referencia (protocolo completo en `protocolo_baseline.json`):

| ID | Baseline | Tipo | Estado |
|---|---|---|---|
| B0 | Persistencia (último valor observado) | regresión | medido hoy (nacional) |
| B1 | Media histórica / naive estacional | regresión | media medida hoy; estacional pendiente (requiere >1 año) |
| B2 | Clasificador por umbral climático (regla) | clasificación | definido, sin ground truth |
| B3 | Clase mayoritaria / aleatorio | clasificación | definido, sin etiquetas |
| — | Modelo ML (scikit-learn / XGBoost + SHAP) | regresión/clasificación | **no entrenable aún** |

Un modelo de Fase 3 solo será adoptado si **supera a B0/B1** en validación
temporal. Hoy la comparación posible es solo contra B0/B1 a nivel nacional.

---

## 4. Protocolo de métricas y validación (experimento D)

- **Unidad de predicción objetivo:** municipio + semana epidemiológica.
- **Métricas de regresión:** MAE, RMSE, MAPE.
- **Métricas de clasificación:** precisión, recall, F1, ROC-AUC.
- **Métricas de producto:** NFR-001 (precisión espacial ≥ 75% en zona piloto)
  y NFR-002 (anticipación mínima de 2 semanas).
- **Validación:** split temporal / walk-forward. **Nunca split aleatorio**,
  para no filtrar información entre semanas.
- **Requisito mínimo de datos:** serie municipio-semana de casos (idealmente
  ≥ 1 año por municipio).

---

## 5. Resultados medibles de esta entrega

### 5.1 Experimento A — Persistencia nacional

Serie nacional de dengue, 13 semanas → **12 transiciones** de un paso
(`ŷ(t) = y(t-1)`):

| Métrica | Valor |
|---|---:|
| MAE | **8.83 casos** |
| RMSE | **11.82 casos** |
| MAPE | **70.68 %** |

Un MAPE de ~71% sobre una serie nacional provisional es, en sí mismo,
evidencia de que la serie corta y ruidosa **no permite afirmar capacidad
predictiva** todavía. Detalle en `expA_persistencia_nacional.csv`.

### 5.2 Experimento B — Modelos walk-forward (nacional)

Ventana inicial de 5 semanas, 8 objetivos evaluados con reentrenamiento
expansivo de un paso:

| Modelo | Objetivos | MAE | RMSE | MAPE |
|---|---:|---:|---:|---:|
| Tendencia lineal | 8 | 10.25 | 15.05 | 108.41 % |
| Persistencia | 8 | 10.75 | 13.86 | 95.24 % |
| Media expansiva | 8 | 11.43 | 13.40 | 81.30 % |
| AR(1) | 8 | 12.07 | 14.46 | 96.68 % |

**Lectura:** ningún modelo supera de forma consistente a la persistencia
(la tendencia gana en MAE pero pierde en RMSE y MAPE; AR(1) es el peor).
Todos los MAPE superan el 80%, es decir, **no hay señal explotable** con 13
puntos nacionales. Detalle en `expB_modelos_nacional.csv` y
`expB_resumen_modelos.csv`.

---

## 6. Experimento C — Regresión cross-sectional: por qué el modelo municipal no es defendible

Se intentó el modelo más simple posible (clima del periodo → casos
acumulados) para dejar **evidencia numérica** de su inviabilidad:

| Enfermedad | Modelo | n | Parámetros | Gl. residual | R² | R² ajust. | LOOCV | LOOCV MAE |
|---|---|---:|---:|---:|---:|---:|---|---:|
| Dengue | Media (intercepto) | 4 | 1 | 3 | 0.000 | 0.000 | válido | **7.67** |
| Dengue | Temperatura | 4 | 2 | 2 | 0.013 | **-0.480** | válido | 13.98 |
| Dengue | Temp + Hum + Precip | 4 | 4 | **0** | **1.000** | — | inválido | — |
| Malaria | Media (intercepto) | 3 | 1 | 2 | 0.000 | 0.000 | válido | **149.00** |
| Malaria | Temperatura | 3 | 2 | 1 | 0.001 | **-0.998** | inválido | — |
| Malaria | Temp + Hum + Precip | 3 | 4 | **-1** | **1.000** | — | inválido | — |

**Hallazgos (evidencia de fallo, no de éxito):**

1. El modelo con las 3 variables climáticas alcanza **R² = 1.000** con
   **0 grados de libertad** (dengue) y **gl = -1** (malaria): es un ajuste
   perfecto por sobreajuste, **sin capacidad de generalizar**.
2. Con una sola variable (temperatura), el **R² ajustado es negativo**
   (-0.48 y -0.998) y el **LOOCV MAE es peor que predecir la media**
   (13.98 vs 7.67 en dengue).
3. Para malaria, incluso el modelo de una variable queda **sin validación
   cruzada posible** (n=3).

**Conclusión:** la regresión cross-sectional **no es un modelo de línea base
válido** con n=4/n=3. Se registra como experimento fallido y como la
justificación técnica de por qué el baseline municipal debe esperar a la serie
municipio-semana. Detalle en `expC_cross_sectional.csv`.

---

## 7. Registro de experimentos (incluidos los fallidos)

| ID | Experimento | Hipótesis | Resultado | Decisión | Estado | Evidencia |
|---|---|---|---|---|---|---|
| EXP-01 | EDA climático (SENAMHI) | Los datos climáticos son utilizables | 16.778 RAW, 274 municipio-día | Continuar pipeline | **Éxito** | `eda_inicial.md` §4-8, `scripts/eda_climatico_output/` |
| EXP-02 | Pipeline de limpieza e imputación | La imputación mejora la cobertura | 43/44 filas `confianza_normal`, 0 `datos_insuficientes` | Adoptar pipeline | **Éxito** | `pipeline_datos.md` §3, `scripts/limpieza_datos.py` |
| EXP-03 | Imputación por mediana histórica | Hay historia suficiente | < 1 año de datos → no aplicable | Declarar no aplicable, no forzar | **Bloqueado (dato)** | `pipeline_datos.md` §2.3 |
| EXP-04 | EDA integrado: clima del periodo ↔ casos acumulados | Existe relación clima-enfermedad | Correlaciones inconsistentes (n=4 / n=3) | No usar para inferencia; pasar a serie temporal | **Hipótesis no sostenida** | `eda_inicial.md` §13-14 |
| EXP-05 | Baseline A: persistencia nacional | La persistencia da referencia útil | MAE 8.83 / MAPE 70.68% | Registrarla como referencia débil | **Éxito parcial (débil)** | `expA_persistencia_nacional.csv` |
| EXP-06 | Baseline B: modelos walk-forward nacionales | Algún modelo supera a persistencia | Ninguno de forma consistente; MAPE > 80% | No adoptar modelo nacional | **Sin mejora** | `expB_resumen_modelos.csv` |
| EXP-07 | Baseline C: regresión cross-sectional municipal | Se puede modelar con n=4/n=3 | R²=1 con 0 gl; LOOCV peor que la media | Descartar como baseline | **Fallo** | `expC_cross_sectional.csv` |
| EXP-08 | Baseline D: protocolo municipio-semana | — | Protocolo definido | Ejecutar cuando existan datos | **Pendiente de datos** | `protocolo_baseline.json` |

Ningún fallo se oculta: los experimentos 03, 04, 06 y 07 son evidencia que
**define qué falta** y **evita** elegir variables o modelos a partir de
correlaciones espurias.

---

## 8. Qué desbloquea la línea base real

| Falta | Desbloquea |
|---|---|
| Serie **municipio-semana** de casos (SEDES/Ministerio) | EXP-08: modelo municipal + NFR-001/NFR-002 medibles |
| Segundo año de clima | B1 naive estacional y mediana histórica (EXP-03) |
| Catálogo oficial de municipios | Validación COM-01 completa (`reglas_calidad_datos.md`) |
| Zona piloto confirmada (`design.md` §10) | Evaluación espacial de NFR-001 |

---

## 9. Reproducibilidad

```bash
python scripts/linea_base_modelo.py
```

Requiere `pandas`, `numpy` y `matplotlib` (`requirements.txt`) y que existan
`data/processed/dengue_semanal_validado.csv` y
`data/processed/dataset_integrado_municipal.csv`. No requiere red ni
credenciales. Salidas en `scripts/linea_base_output/`:

```text
expA_persistencia_nacional.csv
expA_persistencia_nacional.png
expB_modelos_nacional.csv
expB_resumen_modelos.csv
expB_comparacion_modelos.png
expC_cross_sectional.csv
expC_inviabilidad_municipal.png
protocolo_baseline.json
resumen_baseline.json
linea_base_nacional.png
```

Para una lectura ordenada de estos resultados (tablas, gráficos y explicación
de walk-forward, modelos y LOOCV), ver [`resultados_linea_base.md`](./resultados_linea_base.md).

---

## 10. Limitaciones (explícitas)

- La referencia numérica (A y B) es **nacional y provisional**; no mide el
  objetivo del producto (municipio-semana).
- NFR-001 y NFR-002 **no son medibles** todavía: siguen como objetivos de
  diseño.
- El experimento C demuestra inviabilidad, no un resultado predictivo.

---

## 11. Transparencia de IA

- **Herramienta usada:** asistencia de IA (opencode / Claude) para estructurar
  el script `linea_base_modelo.py` y este documento.
- **Qué se revisó humanamente:** los datos de entrada son reales y de
  fuentes oficiales ya validadas por el equipo; el iIvonne Colque debe
  revisar los parámetros (ventana inicial = 5, modelos comparados) y ejecutar
  el script para confirmar los números antes de presentar.
- **Qué NO se delegó:** la decisión de qué se considera evidencia válida, la
  interpretación de los resultados y su aprobación final.
