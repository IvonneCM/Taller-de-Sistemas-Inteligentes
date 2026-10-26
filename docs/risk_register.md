# REGISTRO INICIAL DE RIESGOS

## Proyecto

**Sistema de Predicción Temprana de Dengue y Malaria en Bolivia**


------------------------------------------------------------------------

## 1. Objetivo

Identificar, evaluar y priorizar los principales riesgos que pueden
afectar el desarrollo del proyecto, la calidad e integración de los
datos, la reproducibilidad del proceso y el uso de Inteligencia
Artificial, estableciendo medidas de mitigación que permitan reducir su
probabilidad o impacto.

------------------------------------------------------------------------

## 2. Categorías de riesgo

Para el registro inicial se consideran las siguientes categorías:

-   **Datos:** riesgos relacionados con calidad, disponibilidad,
    cobertura, valores faltantes, valores atípicos e integración de las
    fuentes.
-   **Técnico:** riesgos asociados con scripts, dependencias,
    reproducibilidad, fuentes externas e integración del pipeline.
-   **IA:** riesgos relacionados con el desempeño, generalización,
    interpretación y uso responsable de modelos y herramientas de
    Inteligencia Artificial.

------------------------------------------------------------------------

## 3. Escala de Probabilidad

  -----------------------------------------------------------------------
  Valor                   Nivel                   Descripción
  ----------------------- ----------------------- -----------------------
  1                       Baja                    Es poco probable que el
                                                  riesgo ocurra durante
                                                  el desarrollo del
                                                  proyecto.

  2                       Media                   El riesgo puede ocurrir
                                                  bajo determinadas
                                                  condiciones.

  3                       Alta                    Existe una posibilidad
                                                  considerable de que el
                                                  riesgo ocurra.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Escala de Impacto

  -----------------------------------------------------------------------
  Valor                   Nivel                   Descripción
  ----------------------- ----------------------- -----------------------
  1                       Bajo                    La afectación es menor
                                                  y no compromete los
                                                  resultados principales.

  2                       Medio                   Puede ocasionar
                                                  reprocesamiento,
                                                  retrasos o afectar
                                                  parcialmente los
                                                  resultados.

  3                       Alto                    Puede comprometer la
                                                  calidad de los datos,
                                                  la reproducibilidad, el
                                                  modelo o la
                                                  interpretación de
                                                  resultados.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 5. Cálculo del nivel de riesgo

Para priorizar cada riesgo se utiliza:

**Puntaje de riesgo = Probabilidad × Impacto**

Los puntajes se interpretan de la siguiente manera:

  Puntaje   Nivel de riesgo   Prioridad
  --------- ----------------- -------------------------------------------
  1 - 2     Bajo              Seguimiento normal
  3 - 4     Medio             Seguimiento periódico
  6         Alto              Atención prioritaria
  9         Crítico           Atención inmediata y seguimiento continuo

------------------------------------------------------------------------

## 6. Matriz de Probabilidad × Impacto

Esta matriz determina el nivel de riesgo a partir del cruce entre
probabilidad e impacto.

  Probabilidad ↓ / Impacto →      Bajo (1)   Medio (2)      Alto (3)
  ---------------------------- ----------- ----------- -------------
  **Alta (3)**                   3 - Medio    6 - Alto   9 - Crítico
  **Media (2)**                   2 - Bajo   4 - Medio      6 - Alto
  **Baja (1)**                    1 - Bajo    2 - Bajo     3 - Medio

------------------------------------------------------------------------

## 7. Registro de riesgos

  -------------------------------------------------------------------------------------------------------
  ID      Descripción del    Categoría        Prob.    Impacto    Puntaje Nivel         Mitigación
          riesgo                                                                        
  ------- ------------------ ----------- ---------- ---------- ---------- ------------- -----------------
  R01     Los datos          Datos                3          3          9 **Crítico**   Aplicar procesos
          epidemiológicos                                                               de validación,
          pueden contener                                                               limpieza e
          valores faltantes,                                                            imputación;
          inconsistencias o                                                             documentar los
          registros                                                                     criterios
          incompletos que                                                               utilizados y
          afecten el                                                                    conservar
          análisis y                                                                    evidencia de la
          posteriormente el                                                             calidad de los
          entrenamiento de                                                              datos.
          los modelos.                                                                  

  R02     La cobertura       Datos                3          3          9 **Crítico**   Calcular
          temporal y                                                                    indicadores de
          geográfica de los                                                             cobertura,
          datos climáticos                                                              identificar
          puede ser                                                                     semanas con baja
          insuficiente para                                                             confianza y
          algunos municipios                                                            evitar
          o semanas                                                                     interpretar datos
          epidemiológicas.                                                              incompletos como
                                                                                        observaciones
                                                                                        completas.

  R03     Los valores        Datos                2          3          6 **Alto**      Aplicar controles
          climáticos                                                                    de calidad y
          extremos o                                                                    detección de
          atípicos pueden                                                               valores
          corresponder a                                                                sospechosos antes
          errores de                                                                    de realizar
          medición o                                                                    agregaciones,
          registros anómalos                                                            análisis o
          y afectar los                                                                 entrenamiento.
          resultados.                                                                   

  R04     Cambios en         Técnico              2          3          6 **Alto**      Utilizar Git para
          scripts,                                                                      el código, DVC
          dependencias o                                                                para el
          archivos de                                                                   versionado de
          entrada pueden                                                                datos y un
          dificultar la                                                                 pipeline
          reproducción de                                                               reproducible
          resultados entre                                                              mediante
          integrantes del                                                               `dvc.yaml` y
          equipo.                                                                       `dvc.lock`.

  R05     La disponibilidad  Técnico              2          2          4 **Medio**     Mantener copias
          o estructura de                                                               versionadas de
          las fuentes                                                                   los datos
          externas de datos                                                             utilizados,
          puede cambiar                                                                 documentar las
          durante el                                                                    fuentes y
          desarrollo del                                                                desacoplar el
          proyecto.                                                                     procesamiento de
                                                                                        la descarga de
                                                                                        datos.

  R06     La integración de  Técnico /            3          3          9 **Crítico**   Validar
          datos climáticos y Datos                                                      municipios y
          epidemiológicos                                                               semanas
          puede producir                                                                epidemiológicas
          asociaciones poco                                                             antes de
          confiables debido                                                             integrar,
          a diferencias de                                                              documentar
          cobertura                                                                     diferencias de
          temporal,                                                                     cobertura y
          geográfica o                                                                  evitar
          granularidad.                                                                 interpretar
                                                                                        correlaciones con
                                                                                        muestras pequeñas
                                                                                        como relaciones
                                                                                        causales.

  R07     El modelo de IA    IA                   3          3          9 **Crítico**   Evaluar el modelo
          puede presentar                                                               con métricas
          bajo desempeño o                                                              apropiadas,
          poca capacidad de                                                             separar
          generalización                                                                entrenamiento y
          debido a una                                                                  evaluación,
          cantidad limitada                                                             controlar el
          o desbalanceada de                                                            desbalance de
          datos.                                                                        clases y
                                                                                        documentar las
                                                                                        limitaciones del
                                                                                        modelo.

  R08     Las predicciones   IA                   2          3          6 **Alto**      Presentar el
          del modelo pueden                                                             sistema como una
          interpretarse como                                                            herramienta de
          diagnósticos                                                                  apoyo para alerta
          médicos o                                                                     temprana,
          decisiones                                                                    informar sus
          definitivas.                                                                  limitaciones y
                                                                                        mantener revisión
                                                                                        humana en la
                                                                                        interpretación de
                                                                                        resultados.

  R09     El uso de IA       IA                   2          2          4 **Medio**     Registrar el uso
          generativa durante                                                            de herramientas
          el desarrollo                                                                 de IA, realizar
          puede introducir                                                              revisión humana y
          código, análisis o                                                            validar código,
          documentación                                                                 datos y
          incorrecta si sus                                                             conclusiones
          resultados no son                                                             antes de
          revisados.                                                                    incorporarlos al
                                                                                        proyecto.
  -------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 8. Matriz de ubicación de los riesgos

La siguiente matriz permite observar visualmente dónde se encuentra cada
riesgo de acuerdo con su probabilidad e impacto.

  Probabilidad ↓ / Impacto →   Bajo (1)   Medio (2)                Alto (3)
  ---------------------------- ---------- ------------------------ ------------------------------------
  **Alta (3)**                 ---        ---                      **R01, R02, R06, R07** --- Crítico
  **Media (2)**                ---        **R05, R09** --- Medio   **R03, R04, R08** --- Alto
  **Baja (1)**                 ---        ---                      ---

------------------------------------------------------------------------

## 9. Priorización

### Riesgos críticos

**R01, R02, R06 y R07**

Estos riesgos requieren la mayor atención porque combinan una
probabilidad alta con un impacto alto. Están relacionados principalmente
con la calidad y cobertura de los datos, la correcta integración de las
fuentes y la capacidad del futuro modelo de IA para generalizar.

### Riesgos altos

**R03, R04 y R08**

Requieren seguimiento prioritario. Incluyen la presencia de valores
climáticos atípicos, posibles dificultades de reproducibilidad y el
riesgo de interpretar las predicciones del sistema fuera de su propósito
de apoyo.

### Riesgos medios

**R05 y R09**

Requieren controles preventivos y seguimiento periódico. Corresponden a
posibles cambios en las fuentes externas y al uso de herramientas de IA
generativa durante el desarrollo.

------------------------------------------------------------------------

## 10. Acciones de control implementadas o previstas

  -----------------------------------------------------------------------
  Acción                  Riesgos relacionados    Estado
  ----------------------- ----------------------- -----------------------
  Validación y limpieza   R01, R06                Implementado
  de datos                                        
  epidemiológicos                                 

  Control de calidad de   R02, R03                Implementado
  datos climáticos                                

  Identificación de       R02, R06                Implementado
  cobertura semanal y                             
  datos faltantes                                 

  Versionado de datos RAW R04, R05                Implementado
  mediante DVC y                                  
  almacenamiento remoto                           

  Pipeline reproducible   R04                     Implementado
  mediante `dvc.yaml` y                           
  `dvc.lock`                                      

  Evaluación del modelo   R07                     Previsto para etapa de
  mediante métricas                               modelado
  apropiadas                                      

  Documentación de        R08                     Previsto
  limitaciones de las                             
  predicciones                                    

  Declaración de uso de   R09                     En elaboración
  IA y revisión humana                            
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Seguimiento y actualización

El registro de riesgos deberá revisarse durante el desarrollo del
proyecto. Un riesgo podrá cambiar de probabilidad, impacto o prioridad
cuando exista nueva evidencia.

La revisión debe considerar especialmente:

-   cambios o nuevas versiones de las fuentes de datos;
-   resultados de los controles de calidad;
-   modificaciones en el pipeline reproducible;
-   nuevas brechas de cobertura temporal o geográfica;
-   resultados y métricas obtenidas durante el entrenamiento de modelos;
-   nuevas limitaciones identificadas durante las pruebas;
-   uso de herramientas de IA generativa y evidencia de revisión humana.

Cuando un riesgo cambie de nivel o se identifique uno nuevo, deberá
actualizarse este registro junto con las medidas de mitigación
correspondientes.

---

## Actualización al estado del MVP (2026-10-26) — TASK-043

El registro inicial (arriba) es del Sprint 1. Esta sección declara los riesgos y
límites **reales** del sistema tal como está hoy. No sustituye a la matriz
inicial: la complementa con lo que se aprendió al construir el MVP.

| ID | Riesgo o limitación | Estado hoy | Mitigación o decisión | Evidencia |
|---|---|---|---|---|
| M-01 | **El modelo de dengue no supera de forma concluyente a una regla simple** (t+3: F1 0,33 contra 0,48 de "casos recientes"). | Declarado en la interfaz y en los documentos | Se presenta como estimación exploratoria; no se afirma precisión | [`resultados_experimentales.md`](./resultados_experimentales.md) |
| M-02 | **Solo 13 semanas de historia (SE 1-13 de 2026)**: no hay estacionalidad ni validación entre años. | Abierto | Pedir más semanas y años a SEDES/SNIS | `task_012_baseline.md` |
| M-03 | **Malaria sin modelo**: la fuente solo entrega un acumulado por municipio. | Decidido (ADR-005) | Se muestran casos observados, nunca predicciones inventadas | [`ADR-005`](./adr/ADR-005-malaria-acumulado-en-bd.md) |
| M-04 | **La "etiqueta" no es un brote**: se predice "al menos un caso en t+3", no un brote definido. | Declarado | Definir umbral epidemiológico con el equipo de salud | `task_012_baseline.md` |
| M-05 | **Geometría referencial**: los 4 municipios piloto y Santa Rosa (Beni) son cuadrados de ~5 km; los otros 37 usan el límite de OpenStreetMap simplificado a ~110 m. Ninguno es el límite oficial del INE. | Declarado en la interfaz | Reemplazar por polígonos oficiales antes de calcular áreas o distancias | `app/etl/seed_catalogo.py`, `app/etl/ampliar_catalogo.py` |
| M-06 | **Cobertura**: la demo carga los 42 municipios con casos en el Boletín N.º 13 (28 con dengue, 21 con malaria) con `seed_demo --todos-los-municipios`; el resto del país no tiene datos (REQ-017). Sin esa opción, solo la zona piloto de 4. | Mitigado para la demo (ADR-007) | Nuevos municipios entran al ampliar el catálogo, sin cambiar el esquema (NFR-008) | `app/etl/ampliar_catalogo.py`, `docs/guion_demo_y_plan_b.md` |
| M-07 | **Datos provisionales y con retraso de reporte**: la última semana muestra ~39 % de los casos que terminan reportándose. | Abierto | Marcar datos como provisionales; no tratar la última semana como definitiva | `contrato_esquema_bd.md` |
| M-08 | **Brotes confirmados sin fuente**: la tabla existe pero nadie la carga; el historial y la validación retrospectiva (TASK-034) quedan sin evidencia. | Abierto — decisión pendiente del equipo | Definir de dónde salen los brotes confirmados | `design.md` §3 |
| M-09 | **Las alertas dependen del umbral y del modelo**: `evaluacion_alertas` (TASK-015) ya las genera, pero con el umbral por defecto (70 %, referencial) ninguna de las predicciones actuales (15 a 44 %) alerta. La regla «sin variable explicativa no hay alerta» está en la base, en el módulo y en la API. | Resuelto en código; el umbral real lo define el equipo de salud | Un admin lo cambia con `POST /admin/umbrales` y rige en la siguiente evaluación | `app/ml/evaluacion_alertas.py`, `tests/e2e/test_flujo_completo.py` |
| M-10 | **Despliegue incompleto**: la API está en Render con HTTPS y la base en Neon (`/health/ready` respondió `ok` el 2026-10-26), pero (1) despliega `main`, que puede ir detrás de la versión de la demo; (2) la base de Neon no tiene los datos de demostración, así que no se puede iniciar sesión; (3) la interfaz no está publicada; (4) el plan gratuito se duerme y la primera petición tarda ~45 s. | Parcial (TASK-004, ADR-006) | Pasar la versión de defensa a `main`, correr `seed_demo --todos-los-municipios --fecha 2026-03-30` contra Neon y `scripts/smoke_test.py` con `SMOKE_URL`; despertar la API antes de la demo | `docs/guia_despliegue_render_neon.md`, ADR-006 |
| M-11 | **Sesión del navegador**: el refresh token se guarda en `sessionStorage` para no pedir contraseña al recargar; queda expuesto si hubiera XSS. | Aceptado para el MVP | Access token solo en memoria, refresh revocable en el servidor, sin datos de pacientes | `frontend/src/api.js` |
| M-12 | **Clima de dos fuentes**: SENAMHI (observado) y NASA POWER (modelado) no son equivalentes. | Declarado | Comparación documentada en el contrato de datos | `contrato_esquema_datos_procesados.md` §7bis |
| M-13 | **Confianza de la predicción** mide la proporción de datos climáticos faltantes o imputados (NFR-007); **no** mide qué tan bien acierta el modelo. | Declarado en la interfaz ("Confianza de los datos") | No leerla como probabilidad de acierto | `app/ml/prediccion.py` |
| M-14 | **Sin datos de pacientes**: todo es conteo agregado por municipio. Es una protección, y también un límite (no hay detalle individual). | Por diseño (REQ-020) | — | `privacidad_datos.md` |
| M-15 | **Reglas de campañas y recomendaciones provisionales**: los cortes de riesgo (33,33 % y 66,67 %) y los textos de recomendación son decisiones del MVP, no protocolos de SEDES. | Declarado en la API y en la interfaz | Validar con SEDES antes de usarlas para decidir | `docs/decisiones_task_024_025.md` |
| M-16 | **Dependencias con avisos de seguridad**: `python-multipart`, `python-jose` y `starlette`. | **Resuelto** (TASK-035) | Subidos `python-multipart` 0.0.31, `starlette` 1.10.0 y `fastapi` 0.162.0; `python-jose` reemplazado por PyJWT 2.15.1. `pip-audit` y `npm audit` sin hallazgos; imágenes Docker sin graves ni críticas | `docs/revision_seguridad.md` H-1, H-2 y H-7 |
| M-17 | **Límite de intentos de login y cabeceras de seguridad.** | **Resuelto** (TASK-035); límites conocidos | Límite por correo y por IP (en memoria, una instancia), cabeceras en nginx y en la API | `docs/revision_seguridad.md` H-3, H-4 y H-9 |
| M-18 | **Rendimiento de `GET /zonas/riesgo` (NFR-004) solo se cumple con 1 a 5 usuarios simultáneos**: con 350 municipios simulados el p95 fue 423 ms (1 usuario), 1 775 ms (5), 4 229 ms (10) y 11 627 ms (25). La respuesta pesa 5,1 MB y el servidor atiende ~3 peticiones/s. Datos simulados y medición local, no de Render. | Aceptado (TASK-033) | Reducir el peso (simplificar polígonos, geometría aparte o compresión) si se prevé más de 5 usuarios a la vez. Con los 42 municipios reales y los polígonos simplificados, `/zonas/riesgo` pesa 0,16 MB y `/casos/resumen` 0,35 MB (antes 0,9 y 1,7 MB); no se repitió la prueba de carga | `dengue-malaria-prediccion/scripts/prueba_carga_zonas_riesgo.py` y `tasks.md` TASK-033 |
| M-20 | **El ranking por municipio no es creíble todavía**: con 13 semanas, el modelo da 84 % a Santa Cruz de la Sierra (9 casos en total) y 64 % a San Borja (140 casos, el epicentro), y esas alertas salen con confianza "alta" (que mide datos climáticos completos, no acierto; ver M-13). | Declarado | Presentarlo como resultado de una línea base exploratoria (M-01); revisar con más semanas y con una definición de brote (M-04) | `docs/adr/ADR-007-catalogo-ampliado-opcional.md`, `docs/resultados_experimentales.md` |
| M-19 | **Clima de Alto Beni tomado de coordenadas equivocadas**: la primera geocodificación (`municipios_coordenadas.csv`) lo ubicó en la ciudad de La Paz (más de 3.600 m), ~130 km de su ubicación real en tierras bajas. El panel climático de NASA POWER y su predicción (8 %) usan ese clima, así que esa predicción no es confiable. | Declarado | Regenerar el clima con `data/reference/municipios_ubicacion.csv` (corregida) y reentrenar, avisando antes al equipo porque cambia las métricas de `resultados_experimentales.md` | `scripts/geocodificar_limites.py`, `data/reference/` |

Los riesgos M-08 (sin brotes confirmados) y M-10 (despliegue incompleto) bloquean parte de la demostración completa; el
resto son límites que deben decirse en voz alta durante la defensa.

