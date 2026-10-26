# TASK-024/025: contratos de prevención municipal

Implementados en `app/api/routes/campanas.py`, `municipios.py`,
`app/services/prevencion.py`, `reglas_prevencion.py` y
`app/schemas/prevencion.py`. Se registran en `app/main.py`.
Reglas aprobadas: [decisiones_task_024_025.md](decisiones_task_024_025.md).
No se alteran endpoints de zonas, alertas, autenticación, modelos o migraciones.

**Los umbrales de riesgo y las recomendaciones son decisiones provisionales del MVP.
No constituyen protocolos oficiales de SEDES ni sustituyen la evaluación epidemiológica.**

El modelo predice la probabilidad de registrar al menos un caso de dengue,
no la gravedad de un brote. El GET no ejecuta inferencia ni SHAP: consulta
predicciones almacenadas e inmutables, sin fabricar probabilidades ni datos.

## Predicción compartida elegible

Una única consulta SQLAlchemy/PostgreSQL hace JOIN de predicciones, modelos y
enfermedades. Exige enfermedad dengue en el catálogo, coincidencia de
`Modelo.enfermedad_id` con la predicción y un objeto JSONB de metadatos que
contenga `{"enfermedad":"dengue","horizonte_semanas":3}`. El horizonte textual
`"3"`, booleano, ausente o inválido no se acepta ni se convierte a entero.

Se exige además `fecha_estimada_riesgo = fecha_generacion_UTC::date + 21`
y `fecha_estimada_riesgo >= hoy_UTC`. Hoy es elegible. Todos los filtros,
incluido el territorial, se aplican **antes** de `DISTINCT ON (municipio_id)`.
Se elige la mayor fecha de generación, desempatando por ID de predicción
descendente. Una t+4 más reciente no oculta una t+3 válida anterior.

Se reutiliza el nivel almacenado por TASK-014. No se introduce otro
clasificador ni se confunde el umbral de alerta con los cortes de riesgo:
`<33.33 %` bajo, `>=33.33 % y <66.67 %` medio, `>=66.67 %` alto.
La ausencia de predicción nunca se transforma en riesgo bajo.

## Contrato JSON común

Todos los campos siguientes son obligatorios y no nulos en las respuestas.
Los identificadores provienen de PostgreSQL; no se suponen IDs fijos.

| Campo | Tipo JSON / significado |
|---|---|
| `prediccion_id` | integer, registro seleccionado |
| `municipio_id`, `departamento_id`, `enfermedad_id` | integer, claves del catálogo |
| `municipio`, `departamento` | string, nombres almacenados |
| `enfermedad` | string constante `dengue` |
| `horizonte_semanas` | integer constante `3` |
| `probabilidad_pct` | number entre 0 y 100, sin infinitos/NaN |
| `nivel_riesgo`, `nivel_confianza` | string: `bajo`, `medio` o `alto` |
| `fecha_generacion` | string datetime con zona horaria, ISO 8601 |
| `fecha_estimada_riesgo` | string date `YYYY-MM-DD` |

Los campos de identidad, enfermedad y departamento se obtienen de relaciones
existentes. No se exponen credenciales, geometrías referenciales, datos de
pacientes ni explicaciones técnicas SHAP en estos contratos.

## GET /campanas/priorizacion

Sin parámetros de consulta funcionales. Requiere
`Authorization: Bearer <access_token>` y rol `sedes` o `coordinador_municipal`.
El administrador no tiene acceso implícito.

Respuesta **200**: array JSON de `PrioridadCampana`, con los campos comunes y
`posicion` (integer >=1). La posición se calcula sobre el ámbito autorizado.
Orden: alto→medio→bajo, fecha objetivo ascendente, probabilidad descendente,
ID municipal ascendente. El coordinador solo ve su municipio asignado;
SEDES ve todos los municipios elegibles. No hay filtro municipal controlado
por el cliente que permita ampliar ese ámbito.

Si no hay predicciones elegibles en ese ámbito, devuelve **200** con:

```json
[]
```

**401**: identidad ausente/inválida/vencida o token de tipo incorrecto.
**403**: rol no permitido o coordinador sin municipio asignado.

## GET /municipios/{municipio_id}/recursos

Parámetro de ruta `municipio_id`: integer, ID del catálogo. Sin selección de
enfermedad/horizonte por el cliente: siempre dengue t+3.

Respuesta **200**: objeto JSON `RecursosMunicipio`, con los campos comunes y:

| Campo | Tipo JSON |
|---|---|
| `nivel_atencion` | string: `PRIORITARIO`, `PREVENTIVO` o `RUTINARIO` |
| `recomendaciones` | array de strings |
| `nota` | string con la advertencia provisional del MVP citada arriba |

| Riesgo | Nivel | Acciones (strings en el orden indicado) |
|---|---|---|
| alto | PRIORITARIO | Reforzar vigilancia epidemiológica. / Evaluar disponibilidad de insumos. / Priorizar campañas preventivas. / Fortalecer seguimiento de posibles casos. |
| medio | PREVENTIVO | Intensificar seguimiento epidemiológico. / Revisar disponibilidad de recursos. / Fortalecer actividades preventivas. / Mantener seguimiento periódico. |
| bajo | RUTINARIO | Mantener vigilancia epidemiológica habitual. / Continuar actividades preventivas. / Realizar seguimiento periódico. |

Autorización: `admin` puede consultar cualquier municipio; el coordinador solo
el de `usuario.municipio_asignado_id`, leído desde BD por la autenticación existente.
Se comprueba el ámbito antes de consultar existencia o predicciones, evitando
revelar datos de municipios ajenos.

| HTTP | Situación / `detail` |
|---|---|
| 401 | JWT ausente o inválido; comportamiento existente de TASK-017/018 |
| 403 | Rol no permitido (`No autorizado para este recurso`) o ámbito municipal inválido (`No autorizado para este municipio.`) |
| 404 | Municipio inexistente: `No existe el municipio {municipio_id}.` |
| 404 | Municipio existente sin fila elegible: `El municipio no tiene predicción vigente elegible de dengue a t+3.` |
| 422 | ID de ruta no convertible a entero; validación FastAPI |

Los errores de dominio usan el JSON existente `{"detail":"mensaje"}`;
la validación 422 conserva la estructura de errores de FastAPI. Una avería
de BD no se convierte en lista vacía ni en atención rutinaria.

## Pruebas reproducibles

Desde `dengue-malaria-prediccion/`, con el entorno existente de la raíz:

```powershell
../.venv/Scripts/python.exe -B -m unittest discover -s tests/prevencion -p 'test_*.py' -v
```

`test_reglas_prevencion.py` prueba ranking, desempates, recomendaciones,
permisos municipales y contratos Pydantic sin BD. Los datos de ejemplo están
exclusivamente dentro de tests, identificados como tales; no hay datos de
sustitución en servicios ni endpoints.

`test_integracion_prevencion.py` exige dependencias existentes y la variable
`GATOBYTE_TEST_DATABASE_URL` de una base **exclusiva de pruebas** con las
migraciones aplicadas. Nunca la apunta automáticamente a la BD de desarrollo
o producción. No crea esquema ni ejecuta migraciones.

Una vez que el equipo disponga de esa BD, definir la variable con su URL real
en la sesión local y ejecutar el mismo comando. Las pruebas usan JWT y login
reales, consultas PostgreSQL/JSONB, roles y fixtures de ejemplo. Cada test
revierte una transacción exterior; los commits del login quedan dentro de
savepoints. PostgreSQL puede consumir valores de secuencias incluso después
del rollback: esta es otra razón para usar una BD exclusiva de pruebas.

La suite omite integración si faltan dependencias o esa URL explícita. Una
dependencia presente pero rota, un esquema incompleto o una BD inaccesible
producen fallo, no una omisión silenciosa.

Primera ejecución: 19 aprobadas y 27 integraciones omitidas por falta de entorno.

**Validación de integración posterior, 2026-10-26: 46 pruebas aprobadas,
0 fallidas y 0 omitidas**, incluidas las 27 integraciones. Se instalaron en
`.venv` las dependencias declaradas de `requirements-api.txt` y
`requirements-dev.txt`; scikit-learn 1.5.2 ya estaba disponible. No se cambiaron
requirements ni el esquema. `pip check` y Ruff sobre los archivos nuevos
finalizaron sin errores.

La base utilizada fue `gatobyte_task024025_test`, PostgreSQL 16 + PostGIS 3.4,
en el contenedor exclusivo `gatobyte-task024025-test`, con la misma imagen
`postgis/postgis:16-3.4` de la configuración del proyecto. Se publicó solo en
`127.0.0.1` con puerto asignado por Docker y almacenamiento temporal tmpfs,
sin compartir el volumen de Compose. La contraseña se generó aleatoriamente;
las URL y secretos se suministraron solo al entorno de los procesos de
migración y pruebas, sin guardarlos en el repositorio ni mostrarlos en consola.

Las migraciones existentes llegaron a `7c1e5d9a3b42 (head)`. Se verificaron
consultas PostgreSQL/JSONB, registro de routers, respuestas HTTP/JSON, login
JWT real, RBAC, restricción territorial, dengue t+3, vencimiento, metadatos
inválidos, selección posterior al filtrado y recomendaciones por riesgo.
Después de las pruebas, los conteos de `predicciones`, `usuarios`, `modelos`
y `municipios` fueron todos cero. No fue necesario corregir el código.

## Límites y cierre pendiente

- La integración HTTP/PostgreSQL/JWT y OpenAPI se verificó en la base local
  exclusiva indicada arriba. No constituye validación de despliegue ni de
  precisión epidemiológica del modelo.
- `config.py` carga `.env` mediante Settings; JWT sigue leyendo el entorno
  del proceso. Mantener las variables exportadas o suministradas por Compose
  según la configuración existente. No se modificó seguridad global.
- Los metadatos del modelo son opcionales en el esquema; las filas sin ellos
  quedan excluidas. El origen debe registrar correctamente el modelo usado:
  estos endpoints no pueden detectar una atribución falsa pero consistente.
- El catálogo piloto es de cuatro municipios; no se incorporan municipios
  nuevos ni se recalculan predicciones desde estos GET.
- El panel es histórico y la confianza puede usar faltantes como aproximación
  de imputación. Fecha objetivo futura no demuestra frescura de los datos.
- No hay nueva regla de exclusión por confianza, ni inventario o cantidades.
- TASK-024/025 quedan implementadas y verificadas técnicamente. La revisión
  del equipo y la actualización administrativa del backlog son independientes;
  esta validación no modifica los checkboxes de `tasks.md`.
