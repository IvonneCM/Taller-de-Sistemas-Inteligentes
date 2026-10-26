# Resultados experimentales frente a la línea base (TASK-044)

Resumen para la defensa de los resultados del componente inteligente, **incluidos los intentos que no funcionaron**. Los números salen de los documentos fuente enlazados; aquí no se recalcula ni se redondea a favor del modelo.

> **Lectura en una frase:** el modelo de dengue funciona de punta a punta, pero con 13 semanas de datos **no supera de forma concluyente a una regla simple**; es una línea base exploratoria, no un sistema validado.

## 1. Qué se evaluó

| | |
|---|---|
| Modelo | XGBoost binario, uno por horizonte (t+3 y t+4 semanas), enfermedad: **dengue** |
| Etiqueta | `casos_dengue_t_mas_{3,4} > 0`. **No es una definición epidemiológica de brote** |
| Datos | 28 municipios × 13 semanas de 2026 = 364 filas; 24 variables (rezagos y medias móviles) |
| Validación | Walk-forward cronológico, sin mezcla aleatoria. t+3: 4 orígenes (112 predicciones); t+4: 2 orígenes (56) |
| Comparación | Clase mayoritaria y regla "casos recientes" (predecir lo que ya está pasando) |

Fuente: [`task_012_baseline.md`](./task_012_baseline.md), métricas completas en [`task_012_metricas.json`](./task_012_metricas.json).

## 2. Resultado: modelo contra baselines (promedio macro por origen)

### t+3 (el horizonte que publica el sistema)

| Modelo | F1 | ROC-AUC | Brier |
|---|---:|---:|---:|
| XGBoost | 0,3322 | 0,6588 | 0,2780 |
| Clase mayoritaria | 0,0000 | 0,5000 | 0,2200 |
| **Regla casos recientes** | **0,4775** | **0,6913** | 0,4018 |

El modelo **no supera** a la regla simple en F1 ni en ROC-AUC. Sí supera a la clase mayoritaria y tiene mejor Brier que la regla (probabilidades menos extremas).

### t+4

| Modelo | F1 | ROC-AUC | Brier |
|---|---:|---:|---:|
| XGBoost | 0,3785 | 0,6268 | 0,2533 |
| Clase mayoritaria | 0,3000 | 0,5000 | 0,2194 |
| Regla casos recientes | 0,3255 | 0,6215 | 0,5178 |

Supera apenas a la regla en F1 y ROC-AUC y pierde en Brier y en recall: **evidencia no concluyente**.

**Qué significa:** con ROC-AUC cercano a 0,6 el poder de discriminación es bajo. Con 13 semanas y 2 a 4 orígenes de validación no se puede afirmar superioridad ni que el resultado se mantenga en otros años. Estas métricas **no validan NFR-001 ni NFR-002**.

## 3. Intentos que no funcionaron (y por qué se descartaron)

Registro completo en [`resultados_linea_base.md`](./resultados_linea_base.md) y [`linea_base.md`](./linea_base.md).

| ID | Intento | Resultado | Decisión |
|---|---|---|---|
| A | Persistencia nacional (repetir la semana anterior) | MAE 8,83; MAPE 70,68 % | Referencia débil, se conserva como piso |
| B | 4 modelos walk-forward sobre la serie nacional | Ninguno supera al resto de forma consistente | Sin señal con 13 puntos |
| C | Regresión clima → casos acumulados por municipio | R² = 1,0 con 0 o −1 grados de libertad (n = 4 y n = 3) | **Sobreajuste: modelo municipal no defendible**; es lo que llevó a pedir la serie semana por municipio |
| D | Protocolo municipio-semana | Definido | Se implementó después con la serie semanal de dengue (TASK-009 y 012) |

El experimento C es la mejor justificación técnica de por qué el sistema trabaja con series semanales por municipio y no con acumulados.

## 4. Malaria: no hay modelo, y es una decisión, no un olvido

La fuente entrega **un solo acumulado por municipio** (SE 1 a 13), sin semanas. Repartirlo en semanas habría inventado datos y habría dado al modelo rezagos que no existen ([ADR-005](./adr/ADR-005-malaria-acumulado-en-bd.md)). Por eso el sistema **muestra casos observados de malaria, no predicciones**. Volverá a evaluarse si SEDES entrega casos semanales.

## 5. Qué evidencia pueden revisar

| Evidencia | Dónde |
|---|---|
| Métricas, hiperparámetros y entorno de cada modelo | `dengue-malaria-prediccion/app/ml/artifacts/*_metadata.json` |
| Gráficos (métricas, matrices de confusión, ROC y PR, por origen, probabilidades) | [`scripts/task_012_output/`](../scripts/task_012_output/) |
| Predicciones del walk-forward | `scripts/task_012_output/predicciones_walk_forward_t*.csv` |
| Métricas guardadas en la base | tabla `modelos`, columna `metricas_entrenamiento` (JSONB) |
| Pruebas del entrenamiento | `dengue-malaria-prediccion/tests/ml/test_entrenamiento.py` |

No se usó MLflow: el registro de experimentos es la metadata versionada junto a cada artefacto y la tabla `modelos`.

## 6. Qué haría falta para mejorar el resultado

1. Más semanas de historia (hoy solo SE 1 a 13 de 2026) y de otros años para validar la estacionalidad.
2. Una definición epidemiológica de brote (umbral) en lugar de "al menos un caso".
3. Datos semanales de malaria por municipio.
4. Cobertura climática más completa: solo los 4 municipios piloto tienen cruce real de clima y casos.
