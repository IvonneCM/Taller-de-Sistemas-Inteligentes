# Decisiones del MVP: TASK-024 y TASK-025

Estas reglas son decisiones de diseño del MVP de GatoByte, indicadas por la
responsable de TASK-024/025. **No son protocolos oficiales de SEDES ni
recomendaciones clínicas validadas.** Este documento prepara la implementación;
no declara implementados los endpoints ni cambia el estado de las tareas.

## 1. Objetivos

- **TASK-024 — `GET /campanas/priorizacion`:** consultar municipios con
  predicción vigente de dengue a tres semanas, priorizados por riesgo y
  proximidad de la fecha objetivo. Referencias: REQ-011 y `tasks.md`.
- **TASK-025 — `GET /municipios/{id}/recursos`:** consultar una recomendación
  de atención según el riesgo vigente de dengue a tres semanas del municipio.
  No devuelve inventarios, existencias, cantidades ni asignaciones realizadas.
  Referencias: REQ-012 y `tasks.md`.

## 2. Verificación técnica del horizonte

La tabla `predicciones` no contiene una columna de horizonte. Sin embargo:

1. `Prediccion.modelo_id` referencia `modelos.id`.
2. `Modelo.metricas_entrenamiento` es JSONB y almacena los metadatos completos
   mediante `app.ml.entrenamiento.registrar_metricas_bd()`.
3. Los metadatos reales `baseline_dengue_t3_v1_metadata.json` y
   `baseline_dengue_t4_v1_metadata.json` incluyen respectivamente
   `horizonte_semanas: 3` y `horizonte_semanas: 4`, además de `enfermedad`,
   `nombre` y `version`.
4. TASK-014 calcula `fecha_estimada_riesgo` como fecha UTC de generación
   más 21 o 28 días en `calcular_fecha_estimada_riesgo()`.

Por tanto, el esquema permite distinguirlos mediante un JOIN con `modelos`,
sin inferir el horizonte del ID numérico ni solo del nombre del modelo.
Para estos endpoints, una predicción elegible debe cumplir conjuntamente:

- Enfermedad de la predicción y del modelo: dengue, resuelta mediante el
  catálogo; no asumir un `enfermedad_id` fijo.
- Metadatos del modelo presentes y coherentes: enfermedad `dengue` y
  `horizonte_semanas` con valor numérico entero 3.
- Fecha objetivo igual a `(fecha_generacion AT TIME ZONE 'UTC')::date + 21`.

No se acepta t+4 ni se sustituye por t+3 cuando no haya datos. Si falta la
metadata o contradice las fechas/enfermedad, esa fila no es elegible: no se
adivina el horizonte ni se interpreta el problema como riesgo bajo.

**Límite comprobado:** `persistir_predicciones()` verifica que exista el
`modelo_id`, pero no comprueba que coincida con el horizonte o enfermedad del
resultado calculado. Los filtros anteriores detectan incoherencias visibles;
no certifican qué artefacto se ejecutó si se registró información incorrecta
pero internamente consistente. El origen debe respetar el contrato de TASK-014.
No se verificó el contenido de una instancia PostgreSQL en esta revisión.

## 3. Selección de predicción vigente y fechas vencidas

Para ambas tareas se define **vigente elegible** como la última predicción
por municipio de dengue t+3 que cumple los filtros anteriores y cuya fecha
objetivo no ha pasado. El procedimiento es:

1. Filtrar enfermedad, metadatos de horizonte y coherencia de fechas.
2. Excluir `fecha_estimada_riesgo < fecha_actual_UTC`.
3. Entre las filas restantes del municipio, seleccionar la mayor
   `fecha_generacion`; en empate, el mayor `prediccion_id`.

La fecha objetivo de hoy sigue siendo elegible: aún no ha pasado. Se usa
una única fecha UTC por solicitud, coherente con las fechas de TASK-014.
Los filtros se aplican **antes** de seleccionar la última fila: una t+4
más reciente no debe ocultar una t+3 elegible. Una fila vencida nunca se
devuelve; si ninguna es elegible, no hay predicción vigente para estas tareas.

`app.services.predicciones._vigentes()` actualmente selecciona la última
por municipio/enfermedad e ID, pero **no filtra horizonte ni caducidad**.
`listar_zonas_riesgo()` y `predicciones_vigentes_de_zona()` heredan esa conducta.
No se deben reutilizar sus resultados como si ya cumplieran estas reglas ni
filtrar solo después de que hayan descartado otras filas. La implementación
de TASK-024/025 tendrá su consulta específica, sin modificar el servicio de Dilan.

## 4. Clasificación del riesgo

Se reutiliza `app.ml.prediccion.clasificar_nivel_riesgo()` y el nivel
almacenado por TASK-014, sin ejecutar de nuevo el modelo durante el GET:

| Probabilidad de al menos un caso de dengue | Riesgo |
|---|---|
| Menor que 33.33 % | bajo |
| Desde 33.33 % y menor que 66.67 % | medio |
| Desde 66.67 % | alto |

Estos cortes son provisionales. El umbral configurable de alertas es otro
concepto; no sustituye esta clasificación. La ausencia de datos no es riesgo bajo.

## 5. TASK-024: ordenamiento y desempates

Se devuelve como máximo una fila elegible por municipio, ordenada por:

1. Riesgo: alto, medio, bajo.
2. `fecha_estimada_riesgo` ascendente (la más cercana primero).
3. `probabilidad_pct` descendente.
4. `municipio_id` ascendente.

El desempate por `prediccion_id` de la sección 3 selecciona el registro vigente;
es distinto del orden de municipios de esta sección.

Los municipios inexistentes en el catálogo, sin predicción elegible o solo
con predicciones vencidas no aparecen. Si ninguno es elegible, el listado
es vacío. No se rellenan predicciones, fechas ni probabilidades.

## 6. TASK-025: recomendaciones de atención

| Riesgo vigente | Nivel de atención | Recomendación del MVP |
|---|---|---|
| alto | PRIORITARIO | Reforzar vigilancia epidemiológica; evaluar disponibilidad de insumos; priorizar campañas preventivas; fortalecer seguimiento de posibles casos. |
| medio | PREVENTIVO | Intensificar seguimiento epidemiológico; revisar disponibilidad de recursos; fortalecer actividades preventivas; mantener seguimiento periódico. |
| bajo | RUTINARIO | Mantener vigilancia epidemiológica habitual; continuar actividades preventivas; realizar seguimiento periódico. |

- Municipio inexistente: **404**.
- Municipio existente sin predicción vigente elegible: **404**, también si
  solo dispone de t+4, registros vencidos o metadatos no verificables.
- No responder con atención rutinaria para sustituir una predicción ausente.
- Las recomendaciones no certifican disponibilidad de insumos ni significan
  que se haya asignado personal, presupuesto o materiales.

## 7. Seguridad y autorización

Se reutilizan `app.api.deps.get_current_user()`, `require_role()` y
`app.core.database.get_db()`, sin modificar JWT ni el RBAC existente.

- TASK-024: roles `sedes` y `coordinador_municipal`, según `design.md`.
  Por decisión explícita de implementación, el coordinador solo obtiene el
  municipio de `Usuario.municipio_asignado_id`; sin asignación responde 403.
- TASK-025: `admin` o `coordinador_municipal` asignado al ID solicitado.
  Para el coordinador se comprueba `Usuario.municipio_asignado_id`; no se
  confía en un ID enviado por el cliente ni en un claim municipal no validado.
- Sin autenticación válida: **401**. Rol no autorizado o coordinador que
  intenta consultar otro municipio: **403**, antes de exponer información
  municipal. Un coordinador sin municipio asignado no obtiene acceso municipal.
- No existe bypass implícito de administrador en `require_role()`: cada
  endpoint debe declarar sus roles. TASK-024 no añade admin a su lista.
- No se publican datos personales de pacientes ni se modifican predicciones.

## 8. Reutilización, límites y acuerdos restantes

Componentes reutilizables: entidades `Municipio`, `Enfermedad`, `Modelo` y
`Prediccion`; catálogo y relaciones existentes; `obtener_zona()` para validar
municipio; riesgo y fechas de TASK-014; identidad y roles de TASK-017/018.
No se requieren nuevas tablas, columnas o migraciones para expresar estas reglas.

- Los metadatos deben estar efectivamente registrados en PostgreSQL; los JSON
  locales por sí solos no certifican una fila almacenada. Si no están presentes,
  las filas afectadas no son elegibles.
- El catálogo piloto contempla cuatro municipios aunque el modelo puntúe 28.
  No se inventan IDs ni se amplía el catálogo desde estos endpoints.
- El panel termina en marzo de 2026. Una nueva fecha de ejecución no convierte
  observaciones históricas en datos actuales. Filtrar la fecha objetivo no
  demuestra frescura de las entradas ni vigencia epidemiológica.
- TASK-014 estima calidad por features ausentes si no recibe el porcentaje
  real de imputación. No introducir reglas adicionales de exclusión o de
  prioridad por confianza sin una decisión explícita.
- El contrato JSON y mensajes de error se concretan en
  [task_024_025_api.md](task_024_025_api.md) y `app/schemas/prevencion.py`.
- El entorno API/PostgreSQL debe permitir pruebas de integración. Esta decisión
  no acredita conexión a BD, migraciones aplicadas ni pruebas de los endpoints.

## 9. Decisiones pendientes de validación epidemiológica

Requieren revisión especializada los cortes de riesgo, las recomendaciones
de atención, la prioridad relativa de riesgo y proximidad, y la suficiencia
del horizonte t+3 para acciones preventivas. También deben evaluarse calibración,
sesgo de vigilancia, retrasos de reporte y calidad/frescura de datos.

El modelo estima presencia de al menos un caso, no una definición de brote.
SHAP explica su comportamiento, no causalidad. Ninguna de estas decisiones
constituye validación predictiva fuera de muestra ni autorización sanitaria.
