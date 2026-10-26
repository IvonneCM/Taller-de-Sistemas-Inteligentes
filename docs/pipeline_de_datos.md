# Pipeline de datos — un solo comando

**Responsable:** Tania Perez — Frente "Pipeline de datos"
**Relacionado:** [`contrato_esquema_datos_procesados.md`](./contrato_esquema_datos_procesados.md), [`pipeline_datos.md`](./pipeline_datos.md) (Línea Base — Paso 2, versión anterior de este mismo trabajo), [`reglas_calidad_datos.md`](./reglas_calidad_datos.md)

## Cómo correrlo

```bash
cd Taller-de-Sistemas-Inteligentes   # raíz del repositorio
python -m pip install -r requirements.txt   # pandas, numpy, pdfplumber (lee los boletines PDF)
python scripts/pipeline_completo.py
```

No necesita PostgreSQL ni variables de entorno. Trabaja con los CSV de
`data/raw/` y `data/processed/` y con los boletines PDF de `data/boletines/`
(SE03, 05, 06, 07, 08, 09, 13, 14 y 21 de 2026, descargados a mano de
https://www.minsalud.gob.bo — el sitio rechaza las descargas automáticas).
El clima de NASA POWER se baja **una sola vez** y queda en
`data/raw/clima/nasa_power/`; si ese archivo existe, el pipeline no usa la red.

## Qué hace, en orden

```text
1. scripts/limpieza_datos.py
   validación epidemiológica (COM-xx/EPI-xx) + calendario diario global +
   imputación climática (interpolación → mediana histórica → municipio
   vecino → faltante) + reagregación semanal con nivel de confianza.
            ↓
2. scripts/ventanas_temporales_clima.py   [NUEVO]
   rezagos (lag 1-4 semanas) y promedios móviles (2-4 semanas) de
   temperatura, humedad y precipitación, por municipio.
            ↓
3. scripts/integrar_datos.py
   agregación por zona: une clima (periodo completo) con el acumulado
   epidemiológico SE1-13 por municipio piloto.
            ↓
4. scripts/extraer_dengue_semanal.py
   dengue por municipio y semana (28 × 13) del boletín SE13, verificado
   contra los totales impresos.
            ↓
5. scripts/clima_nasa_power.py   [NUEVO]
   clima semanal de reanálisis NASA POWER para los 42 municipios con casos
   (SENAMHI solo cubre 4). Usa data/reference/municipios_coordenadas.csv.
            ↓
6. scripts/extraer_malaria_boletines.py   [NUEVO]
   malaria por bloques de semanas, restando acumulados de los boletines
   SE5, 7, 8, 9 y 13. Verifica filas y totales; marca lo inconsistente.
            ↓
7. scripts/extraer_dengue_revisiones.py   [NUEVO]
   cuánto cambia cada dato de dengue entre boletines (evidencia de riesgo).
            ↓
8. scripts/construir_panel_semanal.py   [v2]
   panel de dengue municipio-semana: clima, rezagos, objetivos t+3 / t+4.
   ES EL DATASET PARA EL MODELO DE DENGUE.
            ↓
9. scripts/construir_panel_malaria.py   [NUEVO]
   panel de malaria por bloques + clima. ES EL DATASET PARA EL MODELO DE MALARIA.
            ↓
10. scripts/validar_contrato.py   [NUEVO]
   comprueba columnas, claves, rangos y que no haya fuga de datos en los
   paneles. Si falla, el pipeline termina con error (los demás pasos solo
   se "omiten").
```

Se ejecuta una sola vez (no está en el pipeline) `scripts/geocodificar_municipios.py`,
que genera `data/reference/municipios_coordenadas.csv` desde OpenStreetMap.
Ese archivo se versiona; si aparece un municipio nuevo, se vuelve a correr
y solo consulta los que faltan.

Cada paso corre como un **proceso independiente** (no una función
importada) para que un error en un paso no tumbe silenciosamente los
demás, y para que cualquiera pueda correr un paso suelto mientras lo
depura: `python scripts/ventanas_temporales_clima.py`.

## Qué pasa si faltan los datos crudos (bloqueo de DVC)

`data/raw/epidemiologia/` y `data/raw/clima/senamhi/senamhi_raw_SE01_13_2026.csv`
están versionados con DVC contra un remoto de DagsHub. En una máquina sin
esas credenciales (`dvc pull` falla — ver `CONTEXT.md`, bloqueo
reconfirmado el 2026-09-17), el pipeline **no se cae**:

- **Paso 1** detecta que falta el crudo epidemiológico, avisa
  explícitamente en la consola, y reutiliza los CSV ya validados de la
  última corrida real en `data/processed/` en vez de abortar — la parte
  climática (que no depende de epidemiología) sigue corriendo normal.
- **Paso 1** también usa `data/processed/control_calidad_clima.csv`
  (ya en el repo, no pasa por DVC) como respaldo de las coordenadas de
  estación si falta el crudo de SENAMHI — son las mismas coordenadas
  reales, solo que leídas de otro archivo disponible.
- **Paso 3** (de Adriana) sí depende de los crudos epidemiológicos
  directamente; si faltan, termina con error, el pipeline lo anuncia
  claramente y **conserva** el `dataset_integrado_municipal.csv` ya
  existente en el repositorio (no lo borra ni lo corrompe).

Al final, el script imprime un resumen de qué paso corrió completo y cuál
se omitió, para que quede explícito en los logs qué tan "real" es la
corrida.

## Verificación de reproducibilidad

Corrido dos veces seguidas el 2026-10-25 (los pasos 1-9, en un entorno limpio
con `requirements.txt` instalado), los **19 archivos CSV/JSON** de
`data/processed/` dieron el mismo hash MD5 en ambas corridas. El único
archivo que cambia es `resumen_calidad_pipeline.md`, y solo en las líneas
"Generado:" (marca de tiempo) y "Duracion de ejecucion:".

También se verificó con DVC: `dvc repro` reconstruye las 11 etapas, deja
`dvc.lock` al día, `dvc status` responde "up to date" y los CSV quedan
idénticos. El crudo de NASA está marcado `persist: true` en `dvc.yaml` para
que DVC no lo borre (y vuelva a descargarlo) en cada `repro`.

Dependen de datos que **no vienen de la red al correr el pipeline**: los PDF de
`data/boletines/`, `data/reference/municipios_coordenadas.csv` y
`data/raw/clima/nasa_power/nasa_power_diario.csv`. Deben estar en el
repositorio (o bajo DVC) para que otra persona reproduzca el resultado.
Si faltan los PDF o `pdfplumber`, los pasos 4, 6 y 7 avisan y conservan la
salida anterior en vez de fallar.
