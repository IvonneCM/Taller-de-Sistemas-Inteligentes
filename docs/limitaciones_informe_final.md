# Limitaciones conocidas del sistema (TASK-036)

Texto consolidado para la sección de limitaciones del informe final, revisado el
26 de octubre de 2026. **TASK-036 permanece abierta:** el informe vive fuera del
repositorio y esta sección debe revisarse e incorporarse al documento entregado.

Se distinguen las limitaciones del MVP, las restricciones de datos y modelos,
los aspectos pendientes de validación final y las mejoras futuras. La existencia
de código o pruebas no acredita por sí sola disponibilidad en el despliegue ni
validez epidemiológica. Esta actualización documental no ejecuta nuevas pruebas,
auditorías de dependencias ni comprobaciones remotas.

## A. Limitaciones conocidas del MVP

### A.1 Sesgo de vigilancia y representatividad
Los casos que el sistema ve son los que se **notifican**. Una zona con mejor
infraestructura de salud o mejor reporte aparece con más casos aunque no tenga más
enfermedad, y una zona con poco reporte puede parecer tranquila. El modelo aprende de
lo notificado, no de lo ocurrido, y puede reforzar esa desigualdad.

- *Qué mitiga hoy:* nada del sesgo en sí. La interfaz presenta el riesgo como apoyo a
  la decisión humana, no como veredicto, y cada alerta muestra las variables que la
  explican para que un técnico pueda cuestionarla.
- *Qué no mitiga:* no hay corrección por capacidad de reporte ni por población.
- *Para reducirlo:* incorporar población y número de establecimientos por municipio.

### A.2 Retraso de reporte
Los datos recientes son provisionales y pueden revisarse. En el análisis de
revisiones disponible, la última semana publicada representa aproximadamente el
39 % del total finalmente notificado; es un resultado del conjunto analizado,
no una tasa universal de completitud (M-07; [contrato de datos procesados](./contrato_esquema_datos_procesados.md)).
Tratar esos valores como definitivos puede subestimar el riesgo reciente.

- *Qué mitiga hoy:* el contrato documenta el carácter provisional de los datos.
  El horizonte de predicción no corrige la incompletitud de las entradas.
- *Qué no mitiga:* el modelo no corrige el retraso; trata las semanas recientes como
  llegan.
- *Para reducirlo:* modelar la curva de completitud del reporte con más semanas de historia.

### A.3 Cobertura climática irregular y calidad de las entradas
La cobertura SENAMHI documentada se limita a **4 estaciones**: Guayaramerín, Ixiamas,
Palos Blancos y San Buenaventura. Los conjuntos epidemiológicos municipales
iniciales incluyen 28 municipios con dengue y 21 con malaria; esa cobertura no
implica disponer de estaciones observadas para todos ellos. El panel de modelado
también utiliza NASA POWER. Las fuentes observada y modelada no son equivalentes
(M-12) ni garantizan la misma representatividad territorial.

- *Qué mitiga hoy:* el módulo de limpieza genera `es_dato_imputado` y el pipeline
  contempla reducir la confianza o no publicar según la proporción de datos
  climáticos faltantes o imputados. Véase la [cobertura climática](./municipios_sin_cobertura_climatica.md).
- *Límite de trazabilidad:* `app/ml/prediccion.py` advierte que el panel NASA POWER
  v2 no conserva la marca de imputación. La estimación automática basada en NaN
  no detecta valores previamente imputados; se requiere aportar el porcentaje
  real del proceso de calidad. No se garantiza identificar todas las imputaciones.
- *Qué no mitiga:* la confianza mide la completitud de los datos, **no** qué tan bien
  acierta el modelo (M-13).
- *Para reducirlo:* pedir las estaciones adicionales de esa lista.

### A.4 Campañas, recursos y alertas

La priorización de campañas y las recomendaciones de recursos utilizan dengue a
t+3, excluyen predicciones vencidas y requieren metadatos y fechas coherentes.
La selección considera primero las predicciones elegibles y después la más
reciente por municipio. La exclusión por datos insuficientes no equivale a riesgo
bajo. Las recomendaciones no constituyen inventarios ni estiman cantidades de
medicamentos, personal o presupuesto.

Los umbrales de riesgo y las recomendaciones son decisiones provisionales del MVP.
No constituyen protocolos oficiales de SEDES ni sustituyen la evaluación epidemiológica.

TASK-015 genera alertas con explicación según umbrales configurables. El valor por
defecto de 70 % es referencial; la presencia o ausencia de alertas depende de los
datos, las probabilidades y la configuración de cada ejecución, no de una
incapacidad permanente para emitirlas.

En TASK-030, `GET /alertas?solo_vigentes=true` considera relevante para planificación
una alerta asociada a la última predicción del municipio y enfermedad entre
**todas** las predicciones, con fecha objetivo mayor o igual a hoy UTC,
justificación con contenido y variables explicativas válidas. Una nueva predicción
sin alerta sustituye a la anterior. El filtro se aplica antes de paginar;
`solo_vigentes=false` u omitido conserva la consulta de alertas emitidas.

Esta selección no restringe el horizonte y difiere de la selección t+3 elegible
de campañas y recursos. **Vigente no significa sin atender ni sin resolver**:
no existe un flujo de atención o resolución de alertas. La fecha objetivo expresa
el horizonte del modelo, no una fecha clínicamente confirmada de un brote.
Véanse [TASK-024/025](./task_024_025_api.md) y [TASK-029/030](./task_029_030_frontend.md).

### A.5 Visualización e interpretación de resultados

El historial muestra predicciones y brotes registrados en tablas independientes.
La correlación y anticipación siguen una regla descriptiva del backend; no son
pruebas de acierto ni validación estadística. La ausencia de brotes registrados
no demuestra que no hayan ocurrido. El contrato no proporciona una serie de
cantidades de casos confirmados para construir una comparación gráfica de conteos.

El panel de alertas utiliza paginación por desplazamiento, sin total ni indicador
de página siguiente; una página completa puede ir seguida de una vacía. Las
inserciones entre consultas pueden desplazar resultados. Los selectores dependen
de los municipios y enfermedades presentes en las respuestas utilizadas como
catálogo; no permiten descubrir registros ausentes de ambas fuentes.

### A.6 Seguridad y autenticación

El sistema dispone de JWT, hash bcrypt, control de acceso por rol, limitación de
intentos de login y cabeceras de seguridad en la API y nginx. La revisión del
26 de octubre de 2026 documenta actualizaciones de dependencias y sustitución de
`python-jose` por PyJWT; los defectos anteriores no se presentan como pendientes.
Los resultados de auditorías y escaneos corresponden a las versiones y fechas
registradas y no garantizan ausencia futura de vulnerabilidades.

Persisten límites documentados: el refresh token en `sessionStorage` es accesible
ante un XSS; los contadores de login residen en memoria por instancia y se pierden
al reiniciar; el bloqueo por correo puede impedir temporalmente el acceso legítimo.
La confianza amplia en cabeceras del proxy permite riesgos sobre el límite por IP
si se accede directamente a la API. La inmutabilidad de predicciones y alertas
se aplica en el código, no mediante un bloqueo de modificaciones en PostgreSQL.
Estos riesgos y sus mitigaciones se detallan en la [revisión de seguridad](./revision_seguridad.md).

### A.7 Despliegue y operación

[ADR-006](./adr/ADR-006-despliegue-render-neon.md) establece Render y Neon y documenta
verificación de HTTPS y conexión a la base el 26 de octubre de 2026. La revisión
de seguridad también registra verificaciones del despliegue. Por tanto, no se
considera pendiente la elección de proveedor ni se afirma que nunca se desplegó.
Esa evidencia fechada no acredita disponibilidad continua ni que cada cambio
posterior esté publicado; esta actualización no verifica el servicio remoto.

Los límites de los planes gratuitos documentados incluyen suspensión por
inactividad, latencia de reactivación, recursos limitados y ausencia de copias de
seguridad garantizadas. El proceso semanal requiere programación externa y
coordinación de secretos y versiones entre servicios. No se garantiza el objetivo
de disponibilidad a partir de una prueba de arranque o de salud.

## B. Restricciones de los datos y modelos

### B.1 Alcance predictivo y territorial

Existen artefactos XGBoost de dengue t+3 y t+4; el horizonte operativo por defecto
del pipeline es t+3. La etiqueta es presencia de al menos un caso en la semana
objetivo, no gravedad, cantidad de casos ni brote epidemiológicamente definido.
La base no incorpora una columna explícita de horizonte: campañas y recursos
verifican los metadatos del modelo y la coherencia temporal de 21 días.

| Limitación | Qué significa | Riesgo |
|---|---|---|
| **Solo 13 semanas de historia (SE 1-13 de 2026).** | No hay estacionalidad ni validación entre años. | M-02 |
| **La etiqueta no es un brote.** Se predice «al menos un caso en t+3». | No hay definición epidemiológica de brote acordada con salud. | M-04 |
| **Malaria sin modelo predictivo operativo.** No hay una serie semanal municipal equivalente disponible para el flujo operativo. | Se muestran casos observados acumulados; los paneles exploratorios por bloques no equivalen a un modelo operativo. | M-03 |
| **Evidencia insuficiente de brotes confirmados.** | La existencia de tablas y de `GET /modelo/desempeno` no acredita el cumplimiento de NFR-001 y NFR-002; se requiere una fuente legítima y suficiente. | M-08 |

- **Zona piloto de 4 municipios** (REQ-017): el alcance del catálogo piloto no debe
  confundirse con los 28 municipios del panel de entrenamiento de dengue. Ninguno
  de esos alcances acredita representatividad ni generalización nacional (M-06).
- **Geometría referencial:** cada municipio piloto es un cuadrado de unos 5 km, no el límite
  oficial del INE; no sirve para calcular áreas ni distancias (M-05).
- **Sin datos de pacientes:** todo es conteo agregado (REQ-020). Es una protección y también un
  límite: no hay detalle individual (M-14).
- **Reglas de campañas y recomendaciones provisionales:** los cortes (33,33 % y 66,67 %) y los
  textos son decisiones del MVP, no protocolos de SEDES (M-15).

### B.2 Explicabilidad mediante SHAP

SHAP está implementado y existe [evidencia de ejecución con modelos reales](./evidencias/shap_alto_beni.md)
para ambos horizontes. Se explican las 24 variables en orden de entrenamiento y
se verifica que valor base más contribuciones coincida aproximadamente con el
margen del modelo. La escala es **log-odds**, no porcentajes ni probabilidad directa.

Las explicaciones describen el comportamiento del modelo, no relaciones causales
ni fiabilidad epidemiológica. Las variables correlacionadas pueden repartirse
la atribución. Un ranking local no equivale a importancia global; los resúmenes
agregados solo describen el subconjunto analizado. La demostración con artefactos
finales y filas del panel no constituye validación fuera de muestra ni reproduce
los modelos históricos de cada origen de evaluación.

XGBoost admite NaN, pero poder explicar una observación incompleta no acredita
datos suficientes para publicar una predicción. El contrato de alertas devuelve
variable y peso sin una escala ni identificación del modelo por alerta; la
interpretación log-odds corresponde al modelo actual y no debe extrapolarse a
otros modelos sin verificación. Las notas antiguas de integración pendiente en
[TASK-013](./task_013_explicabilidad.md) deben leerse junto con la evidencia posterior.

### B.3 Resultados experimentales y condiciones de medición

En la evaluación registrada, t+3 obtuvo F1 0,3322 frente a 0,4775 de la regla
«casos recientes». Los resultados de t+4 tampoco proporcionan evidencia concluyente
de superioridad. Son resultados de esos datos y del protocolo walk-forward,
no propiedades permanentes del algoritmo. No prueban cumplimiento de los objetivos
epidemiológicos ni generalización a otros años. Véanse los [resultados experimentales](./resultados_experimentales.md).

De forma análoga, la prueba local de carga con 350 municipios simulados registró
p95 de 423 ms con un usuario y 4 229 ms con diez (M-18). Estas mediciones señalan
un riesgo de rendimiento bajo esas condiciones; no fijan una capacidad universal
ni describen el rendimiento actual de Render. Requieren repetición cuando cambien
infraestructura, volumen, geometrías o concurrencia.

## C. Aspectos pendientes de validación final

- Confirmar la versión efectivamente desplegada y repetir el flujo integrado:
  autenticación, permisos, historial, alertas con `solo_vigentes`, campañas y recursos.
  La ausencia temporal de usuarios o registros en una instancia es una condición
  de integración o de disponibilidad de datos, no evidencia de falta de implementación.
- Verificar procedencia, actualización y suficiencia de predicciones y brotes
  confirmados usados en la demostración. Sin evidencia epidemiológica suficiente
  no declarar cumplimiento de NFR-001/NFR-002 ni eficacia sanitaria.
- Comprobar la trazabilidad de imputaciones y la calidad real entregada al pipeline,
  así como compatibilidad de versiones ML en el entorno de ejecución final.
- Repetir las comprobaciones necesarias de HTTPS, salud de API/base, programación
  semanal, recuperación de datos y rendimiento en el entorno final. Las incidencias
  temporales de conexión o configuración deben registrarse con entorno y fecha.
- Completar la revisión y firmas del equipo en seguridad. La evidencia histórica
  no equivale a una auditoría de penetración ni sustituye nuevas verificaciones
  tras cambios de dependencias o despliegue.
- Validar con especialistas los umbrales, la interpretación del riesgo y las
  recomendaciones antes de cualquier uso operativo sanitario.

**Coherencia documental:** el [registro de riesgos](./risk_register.md) conserva
en M-10 una referencia a despliegue pendiente que contradice ADR-006 y la revisión
de seguridad posteriores. También contiene cifras de alertas asociadas a una
ejecución concreta. Aquí se mantienen como antecedentes, sin asumir vigencia
actual. No se modifican esos documentos ni el estado de otras tareas.

## D. Mejoras futuras

Como líneas de trabajo posteriores se proponen ampliar la historia y cobertura
observada, obtener series semanales de malaria, incorporar indicadores de
capacidad de reporte y población, modelar el retraso de notificación y sustituir
geometrías referenciales por límites oficiales. La validación epidemiológica y
temporal adicional debe preceder a afirmaciones de utilidad sanitaria.

En el plano técnico se propone evaluar cookies `HttpOnly` con las protecciones
correspondientes, contadores de login compartidos, metadatos de explicabilidad
por alerta, paginación estable, optimización de geometrías, respaldo y restauración.
Un eventual flujo de atención y resolución de alertas requiere requisitos propios;
no debe inferirse a partir de `solo_vigentes`. Estas propuestas no se presentan
como funcionalidades implementadas ni como compromisos ya aprobados.

## Lectura y condición de cierre de TASK-036

Es un **prototipo funcional de apoyo a la decisión**: integra datos, dispone de
modelos explicables de dengue a 3 y 4 semanas, publica por defecto t+3 y genera
alertas con justificación para su consulta autenticada.
**No** es un sistema validado ni sustituye el juicio epidemiológico. Pasar de prototipo a
herramienta de uso real requiere, como mínimo: más años de datos, una fuente de brotes
confirmados, una definición de brote y de umbral acordada con SEDES, y la revisión de
seguridad firmada por el equipo.

Para cerrar TASK-036 se requiere revisar esta consolidación con la evidencia
final del sistema, ajustar las afirmaciones que dependan del entorno o de los
datos efectivamente utilizados e incorporar la sección al informe final entregado.
Esta actualización no declara completada la tarea ni modifica el backlog.
