# Requisitos del Sistema — Predicción Temprana de Brotes de Dengue/Malaria en Bolivia

**Versión:** 1.0
**Fecha:** 2026-08-24
**Proyecto:** Sistema Inteligente de Predicción Temprana de Brotes (SIPTB)
**Tipo:** Proyecto universitario

> ⏸️ **Estado:** esta especificación es la fuente de autoridad del proyecto,
> pero el desarrollo del backend que implementa estos requisitos está en
> pausa hasta cerrar la primera evaluación (ver
> `README.md` → "Cuándo se retoma"). §6.1 se actualizó el 2026-09-17 con las
> exclusiones confirmadas por el estado real de los datos.

---

## 1. Visión general

El sistema tiene como objetivo predecir zonas con riesgo de brote de dengue o
malaria en Bolivia con **3 a 4 semanas de anticipación**, integrando datos
epidemiológicos históricos, datos climáticos públicos y análisis geoespacial.
Su propósito principal es apoyar la **prevención**, permitiendo activar
campañas de fumigación y asignar recursos médicos antes de que ocurra la
propagación de un brote, en lugar de reaccionar cuando ya es tarde.

> Nota: cualquier cifra de precisión, cobertura de datos o desempeño
> mencionada en este documento es **referencial/estimada** para efectos de
> diseño, salvo que se indique lo contrario con una fuente verificable.

## 2. Actores / Usuarios del sistema

| Actor | Rol | Nivel de acceso |
|---|---|---|
| Autoridad de salud pública | Toma decisiones estratégicas, revisa panorama general | Indicadores agregados, zonas críticas, alertas |
| Equipo de prevención del SEDES | Ejecuta campañas de fumigación y prevención | Indicadores agregados + priorización de zonas |
| Médico epidemiólogo | Analiza causas y variables del brote | Datos históricos, variables climáticas, métricas de confianza, explicabilidad |
| Coordinador sanitario municipal | Asigna recursos a nivel local | Vista por municipio, alertas locales, historial de brotes |
| Equipo técnico / administrador del sistema | Mantiene el sistema y los modelos | Acceso completo, gestión de fuentes de datos y modelos |

## 3. Requisitos funcionales

### Predicción y riesgo

- **REQ-001**: El sistema **deberá** calcular y mostrar el nivel de riesgo
  (alto, medio, bajo) de brote de dengue o malaria por zona geográfica
  (municipio o unidad administrativa equivalente).
  *Criterio de aceptación:* dado un conjunto de datos climáticos y
  epidemiológicos válidos de una zona, el sistema clasifica dicha zona en uno
  de los tres niveles de riesgo y persiste el resultado con fecha de cálculo.

- **REQ-002**: El sistema **deberá** generar predicciones de riesgo de brote
  con un horizonte de **3 a 4 semanas** de anticipación respecto a la fecha
  de ejecución del modelo.
  *Criterio de aceptación:* cada predicción almacenada incluye
  `fecha_generacion` y `fecha_estimada_riesgo`, con una diferencia entre 21 y
  28 días.

- **REQ-003**: El sistema **deberá** mostrar, junto a cada predicción, la
  probabilidad estimada de brote y su nivel de confianza (ej. bajo, medio,
  alto, o un valor porcentual del modelo).
  *Criterio de aceptación:* toda predicción visible en el dashboard incluye
  un campo de probabilidad (0-100%) y un campo de confianza asociado.

- **REQ-004**: El sistema **deberá** indicar qué variables influyeron en cada
  predicción (ej. temperatura, humedad, precipitación, casos históricos),
  ordenadas por grado de influencia (explicabilidad del modelo).
  *Criterio de aceptación:* al consultar el detalle de una predicción, el
  usuario técnico visualiza al menos las 3 variables de mayor peso según el
  modelo (ej. mediante valores tipo SHAP o importancia de variables).

- **REQ-005**: El sistema **no deberá** generar alertas de riesgo crítico sin
  una justificación explícita basada en las variables del modelo.
  *Criterio de aceptación:* toda alerta de riesgo alto incluye
  obligatoriamente al menos una variable explicativa asociada; si no existe,
  la alerta no se publica y se registra como incompleta.

### Visualización y dashboard

- **REQ-006**: El sistema **deberá** presentar un mapa de calor de riesgo
  navegable por zona, municipio y departamento.
  *Criterio de aceptación:* el usuario puede alternar el nivel de agregación
  geográfica (zona/municipio/departamento) y el mapa refleja los niveles de
  riesgo vigentes.

- **REQ-007**: El sistema **deberá** ofrecer una vista simplificada de
  indicadores generales para autoridades de salud pública, y una vista
  detallada con datos históricos, variables climáticas y métricas de
  confianza para equipos técnicos/epidemiólogos.
  *Criterio de aceptación:* dos usuarios con roles distintos que inician
  sesión ven conjuntos de información diferenciados según su rol, verificado
  por control de acceso basado en roles (RBAC).

- **REQ-008**: El sistema **deberá** permitir consultar el historial de
  predicciones pasadas y su comparación con brotes confirmados.
  *Criterio de aceptación:* el usuario puede filtrar por zona y rango de
  fechas, y visualizar predicción vs. resultado real cuando este último esté
  disponible.

### Alertas

- **REQ-009**: El sistema **deberá** emitir una alerta cuando una zona supere
  un umbral de riesgo configurable.
  *Criterio de aceptación:* al superarse el umbral definido (ej. probabilidad
  ≥ 70%), se genera un registro de alerta visible en el dashboard y
  disponible para notificación (ej. correo o panel interno).

- **REQ-010**: El sistema **deberá** permitir a un administrador configurar
  los umbrales de alerta por enfermedad y, opcionalmente, por región.
  *Criterio de aceptación:* un cambio de umbral se refleja en la siguiente
  evaluación de riesgo sin requerir despliegue de código.

### Gestión de recursos y campañas

- **REQ-011**: El sistema **deberá** permitir priorizar zonas para campañas
  de fumigación preventiva en función del nivel de riesgo y la fecha estimada
  del posible brote.
  *Criterio de aceptación:* el sistema genera una lista ordenada de zonas
  priorizadas, exportable o consultable desde el dashboard.

- **REQ-012**: El sistema **deberá** apoyar la asignación de recursos médicos
  mostrando zonas de mayor riesgo antes de la fecha estimada del brote.
  *Criterio de aceptación:* el coordinador municipal puede ver, para su
  municipio, una recomendación de nivel de atención (ej. reforzar insumos)
  asociada al nivel de riesgo vigente.

### Datos e ingesta

- **REQ-013**: El sistema **deberá** aplicar mecanismos de limpieza,
  imputación y validación de datos epidemiológicos y climáticos antes de
  usarlos para generar predicciones.
  *Criterio de aceptación:* un conjunto de datos con valores faltantes o
  fuera de rango es procesado por el pipeline de limpieza y no genera errores
  al llegar al modelo; los registros descartados quedan documentados en un
  log de calidad de datos.

- **REQ-014**: El sistema **deberá** permitir incorporar nuevas fuentes de
  datos epidemiológicos o climáticos sin requerir un rediseño estructural.
  *Criterio de aceptación:* agregar una nueva fuente de datos implica
  únicamente crear un nuevo conector/adaptador de ingesta, sin modificar el
  modelo de datos central.

- **REQ-015**: El sistema **deberá** registrar la procedencia (fuente) y
  fecha de actualización de cada dato ingresado, para trazabilidad.
  *Criterio de aceptación:* cada registro climático o epidemiológico
  almacenado incluye `fuente` y `fecha_ingesta`.

### Evaluación y escalabilidad

- **REQ-016**: El sistema **deberá** permitir evaluar el desempeño del
  modelo comparando predicciones históricas contra casos reales confirmados.
  *Criterio de aceptación:* existe una vista/reporte con métricas de
  desempeño (ej. precisión espacial, sensibilidad) calculadas sobre un
  periodo definido por el usuario.

- **REQ-017**: El sistema **deberá** estar diseñado para escalar a nuevos
  departamentos de Bolivia sin cambios estructurales en el modelo de datos.
  *Criterio de aceptación:* agregar un nuevo departamento requiere solo
  cargar sus datos geográficos y epidemiológicos, sin modificar el esquema
  de base de datos.

- **REQ-018**: El sistema **deberá** estar diseñado para incorporar otras
  enfermedades transmitidas por vectores en el futuro (ej. Zika, Chikungunya)
  reutilizando la misma arquitectura de datos y modelos.
  *Criterio de aceptación:* el modelo de datos incluye una entidad
  "enfermedad" desacoplada de la lógica geográfica y climática.

### Seguridad y control de acceso

- **REQ-019**: El sistema **deberá** autenticar a los usuarios y restringir
  el acceso a la información según su rol.
  *Criterio de aceptación:* un usuario no autenticado no puede acceder a
  ningún endpoint de datos; un usuario autenticado solo ve la información
  permitida para su rol.

- **REQ-020**: El sistema **no deberá** exponer datos personales de
  pacientes; solo deberá procesar datos epidemiológicos agregados y
  anonimizados por zona.
  *Criterio de aceptación:* ningún endpoint ni tabla del sistema almacena
  identificadores personales (nombre, CI, dirección exacta de paciente).

## 4. Requisitos no funcionales (NFR)

- **NFR-001 (Precisión espacial):** el modelo deberá alcanzar una precisión
  espacial mínima del **75%** en la zona piloto (cifra objetivo de diseño,
  a validar empíricamente durante las pruebas).
- **NFR-002 (Anticipación mínima):** el sistema deberá anticipar brotes al
  menos **2 semanas** antes de su confirmación clínica en la zona piloto.
- **NFR-003 (Disponibilidad):** el sistema deberá tener una disponibilidad
  objetivo del 99% mensual para el dashboard en el entorno de producción del
  piloto.
- **NFR-004 (Rendimiento del dashboard):** las consultas de mapas de calor y
  listados de riesgo deberán responder en **< 2 segundos (p95)** para
  conjuntos de hasta 350 municipios.
- **NFR-005 (Seguridad):** las contraseñas deberán almacenarse con hash
  (ej. bcrypt/argon2); la comunicación deberá usar HTTPS/TLS en todos los
  entornos desplegados.
- **NFR-006 (Explicabilidad):** toda predicción deberá poder mostrar sus
  variables explicativas en **< 1 segundo** adicional tras la consulta
  principal.
- **NFR-007 (Tolerancia a datos incompletos):** el pipeline de datos deberá
  seguir operando (con predicciones marcadas como de menor confianza) cuando
  hasta un 20% de los registros climáticos de una zona estén ausentes en una
  ventana de tiempo dada.
- **NFR-008 (Escalabilidad):** la arquitectura deberá soportar el
  crecimiento de 1 a 9 departamentos de Bolivia sin cambios en el esquema de
  base de datos (solo en volumen de datos).
- **NFR-009 (Auditoría):** toda alerta emitida y toda predicción generada
  deberán quedar registradas de forma inmutable (solo lectura tras su
  creación) para fines de auditoría y evaluación posterior.
- **NFR-010 (Mantenibilidad):** el código del pipeline de datos y del
  modelo deberá estar cubierto por pruebas automatizadas con una cobertura
  mínima del 70% en los módulos críticos (ingesta, limpieza, predicción).

## 5. Supuestos y restricciones conocidas

- Puede existir **retraso de reporte** en los datos epidemiológicos
  (los casos no siempre se notifican el mismo día en que ocurren).
- Puede existir **sesgo de vigilancia**: zonas con mejor infraestructura de
  salud reportan más casos, lo que no necesariamente indica mayor incidencia
  real.
- Los datos climáticos públicos pueden tener **cobertura irregular** entre
  regiones (ej. menor densidad de estaciones meteorológicas en zonas
  rurales).
- El sistema **no reemplaza el criterio clínico ni epidemiológico**; es una
  herramienta de apoyo a la decisión.
- No se manejarán datos personales identificables de pacientes; todo dato
  epidemiológico se trabaja de forma agregada por zona.

## 6. Fuera de alcance (versión inicial)

- Integración en tiempo real con sistemas hospitalarios o historias clínicas
  electrónicas.
- Aplicación móvil nativa para agentes de campo (se contempla solo dashboard
  web en esta fase).
- Predicción de otras enfermedades distintas a dengue/malaria (queda
  preparado el diseño, pero no implementado en el MVP).
- Notificaciones push en tiempo real vía SMS/WhatsApp (se contempla solo
  alerta visible en dashboard y, opcionalmente, correo electrónico).
- Módulo de logística detallada de fumigación (rutas, inventario de
  insumos); el sistema solo prioriza zonas, no gestiona la logística
  operativa completa.
- Certificación oficial ante el Ministerio de Salud; este es un proyecto
  universitario/piloto, no un sistema de producción certificado.

## 6.1 Exclusiones adicionales confirmadas por el estado real de datos (2026-09-17)

Complemento de la sección 6 aprobado para la presentación (ver
`docs/alcance_exclusiones.md`). Marca explícitamente lo que esta evaluación
**no** entrega, para evitar asumir un alcance que los datos reales no sostienen:

- **Modelo predictivo municipio-semana operativo.** Fuera del alcance de esta
  evaluación: no existe serie temporal semanal de casos por municipio (solo
  acumulados SE1-13). La entrega es una línea base nacional provisional como
  referencia inicial (ver ADR-004). REQ-001/REQ-002 y NFR-001/NFR-002 siguen
  como objetivos de diseño, no medibles todavía.
- **Predicción nacional como entregable operativo.** La serie nacional
  (SE1-13) es provisional (la propia fuente declara el dato "sujeto a
  actualización") y solo sirve como referencia numérica de baselines, no como
  sistema de predicción.
- **Datos históricos mayores a un año.** Solo se dispone de semanas SE1-13 de
  2026 (clima desde SE3). No se puede aplicar estacionalidad ni la regla de
  mediana histórica de calidad del pipeline.
- **Cobertura geográfica más allá de la zona con datos reales.** El análisis
  real opera con 4 municipios (Guayaramerín, Ixiamas, Palos Blancos, San
  Buenaventura). El resto de Bolivia (REQ-017) queda en diseño, no
  implementado.
- **Fuentes de datos aún no confirmadas.** SEDES, SNIS, NASA POWER e INE no
  están incorporadas a esta evaluación; solo están identificadas como
  pendientes (ver `docs/inventario_datos.md`).
- **Datos en streaming / tiempo real.** Todo el flujo opera en modo batch
  por semana epidemiológica; no hay ingesta en tiempo real.
