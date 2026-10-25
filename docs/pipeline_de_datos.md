# Pipeline de datos — un solo comando

**Responsable:** Tania Perez — Frente "Pipeline de datos"
**Relacionado:** [`contrato_esquema_datos_procesados.md`](./contrato_esquema_datos_procesados.md), [`pipeline_datos.md`](./pipeline_datos.md) (Línea Base — Paso 2, versión anterior de este mismo trabajo), [`reglas_calidad_datos.md`](./reglas_calidad_datos.md)

## Cómo correrlo

```bash
cd Taller-de-Sistemas-Inteligentes   # raíz del repositorio
python -m pip install -r requirements.txt   # pandas, numpy
python scripts/pipeline_completo.py
```

No necesita PostgreSQL ni variables de entorno — trabaja solo con los CSV
de `data/raw/` y `data/processed/`.

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
```

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

Corrido dos veces seguidas el 2026-10-25, los 5 archivos de salida que no
dependen de los crudos bloqueados (`clima_semanal_calidad.csv`,
`clima_semanal_ventanas.csv`, `dengue_municipal_validado.csv`,
`malaria_municipal_validado.csv`, `dataset_integrado_municipal.csv`)
dieron el mismo hash MD5 en ambas corridas — el pipeline es reproducible
con los datos disponibles hoy.
