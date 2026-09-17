# ADR-004: Adoptar la línea base nacional como referencia inicial

- **Estado:** Aceptado
- **Fecha:** 2026-09-17
- **Decisores:** Equipo SIPTB
- **Relacionado:** `linea_base.md`, `eda_inicial.md` §13/§16, `requirements.md` (REQ-014, NFR-001, NFR-002), `design.md` §10

## Contexto

El objetivo del sistema es predecir el riesgo de brote de dengue/malaria por
**municipio y semana epidemiológica** con 3-4 semanas de anticipación. Eso
requiere un dataset de modelado con pares `X(t) -> y(t+k)`: clima del municipio
en la semana `t` y casos de la semana `t+k`.

Hoy existe:

- Clima limpio y validado por municipio-semana: **44 filas** (4 municipios x
  SE3-SE13) — `data/processed/clima_semanal_calidad.csv`.
- Casos epidemiológicos **acumulados** SE1-SE13 por municipio: **4 filas** de
  dengue y **3** de malaria — una sola observación por municipio.
- Una **serie semanal nacional** de dengue: **13 semanas** SE1-SE13 (dato que la
  fuente declara *provisional*).

No existe una **serie temporal (semana a semana) de casos por municipio**. El
pipeline de calidad (`scripts/limpieza_datos.py`) dejó lista la variable
predictora (clima), pero no las etiquetas (`y`) en la misma unidad municipio+semana.
Por eso, el objetivo municipal tiene una sola observación por municipio: la tabla
de modelado colapsa a 4 filas (dengue) y 3 (malaria).

## Alternativas consideradas

1. **Entrenar un modelo municipal ahora** — descartado: dataset colapsado (4-3
   filas); no se puede entrenar ni validar, y no hay etiquetas de brote por
   municipio-semana para clasificación.
2. **Adoptar la línea base nacional provisional como referencia inicial** —
   la serie nacional (13 semanas) permite medir baselines B0-B1 hoy, aunque el
   dato sea provisional y no satisfaga NFR-001 (municipio) ni NFR-002 (anticipación).
3. **Generar/inventar la serie temporal** — prohibido por la Regla de Evidencia
   del proyecto; no se inventan datos no verificados.
4. **Dejar la entrega en blanco** — rechazado: se pierde la posibilidad de medir
   y registrar todo lo que sí es calculable hoy.

## Decisión

**Adoptar la línea base nacional provisional como referencia inicial** del
periodo de datos actual, y **diferir el modelo predictivo municipal** hasta
contar con una serie temporal de casos a nivel municipio-semana (o equivalente).
El modelo municipal será adoptado solo si supera B0 (persistencia) y B1 (media
histórica) en validación temporal, tal como define `linea_base.md` §3-§4.

## Justificación

- Es la **única referencia numérica medible hoy**: los baselines B0-B1 se calculan
  sobre la serie nacional (13 semanas), mientras que el objetivo municipal no
  puede validarse ni con split temporal ni con walk-forward sin serie semanal
  (`linea_base.md` §4).
- Mantiene la **Regla de Evidencia**: se mide lo que existe, se declara lo
  provisional como provisional, y se registra explícitamente lo que queda bloqueado
  por la fuente, sin inventar datos ni desempeños.
- Es **consistente con el estado de arte del pipeline**: el clima ya está limpio,
  validado e integrado; falta únicamente el componente epidemiológico temporal,
  que al incorporarse reactivará el resto del flujo sin rediseño.
- Evita presentar como "modelo operativo" algo que no cumple NFR-001/NFR-002.

## Consecuencias

- **Positivas:** referencia numérica inicial reproducible y trazable (exp A-B de
  `scripts/linea_base_output/`); estado explícito y verificable; el bloqueo del
  objetivo municipal queda documentado en vez de silenciado.
- **Negativas / costos:** todavía **no existe modelo municipal operativo**; el
  sistema no puede emitir predicciones de zona ni superar formalmente los
  baselines NFR-001/NFR-002 hasta resolver la fuente temporal.
- **Desbloqueo pendiente:** obtener casos semana-a-semana por municipio (solicitud
  SEDES, boletines semanales acumulativos que permitan derivar incrementos, o
  SNIS) y, con >1 año de datos, reactivar la regla de mediana histórica de calidad.
  Al obtener la serie, ejecutar `scripts/limpieza_datos.py` + `scripts/integrar_datos.py`
  para construir el dataset de modelado municipio-semana.