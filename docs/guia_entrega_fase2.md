# Guía de entrega: de la Fase 1 (datos) a la Fase 2 (modelo XGBoost + SHAP)

**De:** Tania Pérez (pipeline de datos) · **Para:** quien entrene el modelo
**Contrato completo de columnas:** [`contrato_esquema_datos_procesados.md`](./contrato_esquema_datos_procesados.md)
**Fecha:** 2026-10-25

Esta guía es lo mínimo que hay que saber para empezar hoy, sin esperar a nadie.

## 1. Arranque en 3 comandos

```bash
python -m pip install -r requirements.txt
python scripts/pipeline_completo.py       # regenera todo; el último paso valida el contrato
python scripts/validar_contrato.py        # úsalo antes de entrenar y tras cualquier cambio
```

## 2. Qué archivo usar

| Modelo | Archivo | Unidad | Filas |
|---|---|---|---|
| **Dengue** | `data/processed/panel_semanal_dengue_clima.csv` | municipio × semana | 364 (252 utilizables para predecir a 3 semanas) |
| **Malaria** | `data/processed/panel_bloques_malaria_clima.csv` | municipio × **bloque** de semanas | 103 (101 utilizables) |

Son **dos modelos distintos** porque las fuentes tienen granularidad distinta:
dengue es semanal; malaria solo existe en bloques (SE1-5, SE6-7, SE8, SE9, SE10-13),
y un bloque nunca se reparte en semanas. En malaria se predice `casos_por_semana`, no `casos_total`.

## 3. Variable objetivo: decisión que te toca a ti (Fase 2)

El panel entrega candidatos, **no define "brote"**:

| Columna | Úsala si… |
|---|---|
| `casos_dengue_t_mas_3` / `casos_dengue_t_mas_4` | quieres **regresión** (cuántos casos habrá). Horizonte del producto: 3-4 semanas. |
| `hay_casos_t_mas_3` | quieres una **clasificación** simple (¿habrá casos?). No es un brote. |
| (tú la defines) | un umbral de brote. Con 13 semanas no hay historia para un umbral epidemiológico defendible; documenta el criterio que elijas y por qué. |

## 4. Qué columnas usar como entrada y cuáles NO

**Entradas válidas (se conocen antes del momento de predecir):**
`temperatura_media`, `humedad_media`, `precipitacion_total_mm` (de la semana actual),
sus `_lag1..4` y `_media_movil_2/3/4sem`, `casos_dengue`, `casos_dengue_lag1..4`,
`casos_dengue_acum_4sem`, y `semana_epidemiologica` (con cuidado).

**NO usar como entrada (fuga o ruido):**
- `casos_dengue_t_mas_3`, `casos_dengue_t_mas_4`, `hay_casos_t_mas_3`: **son el futuro**.
- `senamhi_*`: existe solo en 4 municipios; es para comparar, no un predictor común.
- `fuente`, `pagina_fuente`, `periodo_dato`, `fuente_clima`, `tiene_clima`: metadatos constantes.
- `municipio` / `departamento` como texto sin codificar: con 28 municipios invita a memorizar.

`scripts/validar_contrato.py` comprueba que los objetivos y rezagos salgan de la semana correcta.

## 5. Cómo validar (importante)

- **Separa por tiempo, no al azar.** Entrena con SE anteriores y prueba con las últimas semanas;
  una partición aleatoria deja que el modelo "vea" semanas vecinas del mismo municipio.
- Con un solo año y 13 semanas **no hay validación entre años**. Las métricas sirven para probar
  que el código funciona, **no como evidencia de desempeño**. Dilo así en la presentación.
- Compara siempre contra una **línea base**: "los casos de la semana actual" ya da una
  correlación de 0,75 con los casos a 3 semanas y MAE 0,88 (media global: 1,42). Un modelo que no
  la supere no aporta.

## 6. Lo que ya sabemos que va a pasar (para no sorprenderse)

1. **El clima casi no predice.** Correlación con los casos a 3 semanas: temperatura 0,08,
   humedad 0,21, lluvia 0,02. Domina el nivel actual de casos. SHAP lo mostrará; es un resultado
   honesto de los datos, no un error del modelo.
2. **Pocos municipios mueven todo.** San Borja (140 casos) y Caranavi (60) concentran la mayoría;
   solo 96 de 252 filas tienen casos > 0 en el objetivo.
3. **El clima es de reanálisis (NASA POWER), no de estación.** Bueno para temperatura (r = 0,69 contra
   SENAMHI), débil para lluvia semanal (r = 0,40).
4. **El dato reciente se corrige después.** La última semana de un boletín trae ~39 % de los casos
   finales; con 1 semana de antigüedad, ~77 %; desde 2 semanas, ~95 %
   (`data/processed/dengue_revisiones_resumen.csv`). En producción `casos_dengue_lag1` estará
   subestimado respecto al dato con el que se entrena.
5. **Los ceros de municipios ausentes no son ceros**: 14 municipios con malaria no aparecen en la
   tabla de dengue (se desconoce si no hubo casos o no se reportó).

## 7. Cuando haya datos reales

Cuando SEDES/SNIS entregue historia por municipio, solo hay que volver a correr el pipeline:
el contrato (nombres y tipos de columna) no cambia. Reentrenar con `python scripts/pipeline_completo.py`
+ tu script de entrenamiento. Mientras tanto:

- Haz que tu script de entrenamiento lea las columnas **por nombre** (no por posición) y sea
  independiente del número de filas.
- Si el contrato necesita cambiar, avisa en el mismo commit (`validar_contrato.py` y el contrato se actualizan juntos).

## 8. Para quien actualice el Risk Register (Fase 9)

Evidencia concreta de esta etapa, con archivo que la respalda:

| Riesgo de datos | Evidencia |
|---|---|
| Muestra insuficiente (1 año, 13 semanas) | `panel_semanal_dengue_clima.csv`: 364 filas |
| Dato provisional que se corrige | `dengue_revisiones_resumen.csv`: 35 % / 24 % / 16 % / 13 % del dato final faltaba en los boletines SE5 / 7 / 8 / 9 |
| Sin serie semanal de malaria | `malaria_municipal_bloques.csv`: solo SE8 y SE9 son semanas |
| Error en la fuente oficial | Boletín SE5: San Buenaventura imprime 1 vivax y total 0 (`malaria_acumulado_por_boletin.csv`, `fila_inconsistente`) |
| Clima modelado ≠ observado | Comparación NASA POWER vs SENAMHI (contrato §7bis) |
| Fuente que bloquea descargas automáticas | El sitio del Ministerio rechazó 28 descargas; los boletines se bajaron a mano |
| Sin respuesta de SEDES/SNIS | Historia 2019-2025 pendiente: es la dependencia que bloquea un modelo real |
| Dependencia de credenciales DVC | `data/raw/` está en DagsHub; sin credenciales `dvc pull` falla |
| Cobertura geográfica | 14 municipios con casos no tienen datos en dengue; SENAMHI cubre 4 de 28 |
