# TASK-029 y TASK-030: historial y alertas emitidas

## Estado y alcance

Se completaron los componentes existentes `Historial.jsx` y `Alertas.jsx`,
sin crear pantallas paralelas ni modificar JWT, modelos, migraciones
o fuentes de datos. La extensión compatible de `/alertas` se describe abajo.
`App.jsx` transmite a ambos el filtro global de enfermedad.
Se reutilizan `pedir()`, `useCarga()`, los formateadores, insignias y estados
de carga, error y vacío. No se agregaron dependencias al proyecto.

La implementación y las pruebas de frontend están completas. La demostración
manual con registros epidemiológicos reales queda condicionada a su carga
legítima en el backend; los tests no sustituyen esa evidencia. No se cambian
los checkboxes del backlog ni se declara validación epidemiológica.

## TASK-029: contrato y comportamiento

La vista técnica conserva el selector municipal y agrega fechas Desde/Hasta,
los botones Aplicar fechas y Limpiar fechas, y validación de rango. No se
consulta un rango cuya fecha inicial sea posterior a la final. Se admiten
rangos abiertos e inclusivos; editar fechas no dispara peticiones hasta aplicar.

Se llama a `GET /zonas/{municipio_id}/historial` con los parámetros reales:

| Parámetro | Significado |
|---|---|
| `enfermedad_id` | ID recibido del backend para la enfermedad seleccionada |
| `desde`, `hasta` | Fechas ISO `YYYY-MM-DD`; `pedir()` omite valores vacíos |

La respuesta contiene `predicciones`, `brotes_confirmados` y
`ventana_correlacion_dias`, además de información municipal y filtros.
Se muestran dos tablas independientes:

- Predicciones: fecha de generación, enfermedad, nivel de riesgo,
  probabilidad, fecha objetivo, correlación con brote y anticipación.
- Brotes registrados: fecha de confirmación, enfermedad y fuente. Se muestran
  incluso si no hay predicciones en el rango consultado.

La correlación es la regla descriptiva del backend: misma enfermedad y zona,
con confirmación a no más de la ventana indicada respecto de la fecha objetivo.
No se presenta como predicción acertada ni precisión estadísticamente validada.
La anticipación es la diferencia entre generación y confirmación; si resulta
negativa se indica que la confirmación fue anterior, sin convertirla en una
anticipación positiva. Un valor ausente se muestra como no disponible.

Las fechas filtran generación de predicciones y confirmación de brotes en UTC.
La correlación usa todos los brotes de la zona, por lo que puede referenciar
uno fuera del rango de la segunda tabla. Las fechas de generación se presentan
con el formateador existente de La Paz; los filtros mantienen semántica UTC.

Ausencia de brotes registrados **no demuestra ausencia real de brotes**.
No se inventan cantidades de casos ni se generan gráficos de cantidades:
este endpoint no proporciona esa serie temporal.

## TASK-030: contrato y comportamiento

El panel conserva sus tarjetas y muestra **alertas emitidas**, con selector
«Todas las emitidas» (inicial) o «Vigentes para planificación». El segundo
consulta el filtro real del servidor; no calcula la vigencia en el navegador.
Vigente no significa pendiente de atención ni no resuelta.

Se utiliza `GET /alertas` con:

| Parámetro | Uso |
|---|---|
| `enfermedad_id` | Filtro global de enfermedad, con ID real |
| `municipio_id` | Selector opcional; vacío significa todos los municipios |
| `desde`, `hasta` | Fechas inclusivas de emisión UTC, aplicadas tras validación |
| `limite` | 50 registros por página, dentro del rango admitido 1–500 |
| `desplazamiento` | 0, 50, 100… según la página solicitada |
| `solo_vigentes` | `false` para todas; `true` para vigentes para planificación |

La API ordena por fecha de emisión e ID descendentes. La vista preserva ese
criterio y ordena también cada página recibida por esas claves. Muestra
municipio, enfermedad, riesgo, probabilidad, umbral, fecha de emisión,
fecha estimada de riesgo, justificación y
todas las variables con sus pesos numéricos y signo, redondeados a cuatro
decimales. Un peso no numérico no se sustituye por cero.

En el XGBoost actual, TASK-013 calcula SHAP en **log-odds**: los signos
indican contribuciones al margen respecto de la base, no porcentajes ni
causalidad. El contrato de `/alertas` solo devuelve `{variable, peso}`:
**no incluye escala ni identificación del modelo por alerta**. La interfaz
explicita que esa interpretación corresponde al modelo actual; no certifica
escalas de futuros modelos. No modifica el texto de justificación del servidor.

La paginación ofrece Anterior/Siguiente. Siguiente se habilita con una página
completa; al no existir total o `has_more`, la siguiente puede estar vacía.
En ese caso se permite volver, sin afirmar que se conoce el número total.
El cambio de municipio, fechas o vigencia reinicia la página. Las inserciones entre
consultas pueden desplazar elementos: es una limitación de la paginación por
offset del contrato, no una consulta sobre un snapshot estable.

## Integración, catálogos y seguridad

`App.jsx` combina los registros ya recibidos de `/zonas/riesgo` y
`/casos/resumen`. `datosPaneles.js` extrae IDs verificables de enfermedad y
opciones municipales sin asumir IDs fijos. Esto permite consultar historial
de municipios con casos aunque no tengan predicciones actuales.

Si la enfermedad no aparece en esas respuestas, o sus IDs son contradictorios,
no se adivina un ID ni se consultan otras enfermedades como sustitución. Se
muestran carga/error/vacío según corresponda. El selector no puede descubrir
municipios que no aparezcan en ninguna de esas dos respuestas: no existe una
consulta nueva de catálogo en esta implementación.

El cambio global de enfermedad reinicia los filtros y la página de ambos
paneles. No afecta el mapa ni sus consultas.

Se conserva la sesión y el cliente HTTP existentes: access token en memoria,
refresh y manejo de 401/403. Solo epidemiólogo y administrador ven/consultan
el historial desde la UI; el backend mantiene la restricción efectiva. Las
alertas mantienen el acceso autenticado existente. No se amplían permisos.

## Evidencia automatizada y reproducción

Suite ejecutada con Node **24.17.0**, ya instalado, mediante un PATH local al
proceso; no se cambió el Node global. El proyecto exige Node >=22.12.0.
Se instalaron exclusivamente las dependencias fijadas mediante `npm ci`,
sin cambios a `package.json` o `package-lock.json`.

Desde `dengue-malaria-prediccion/frontend/`, con Node compatible:

```powershell
npm test
npm run build
```

- **136 pruebas de frontend aprobadas, 0 fallidas**, en 8 archivos.
- `Historial.test.jsx`: renderizado, tablas independientes, municipio,
  enfermedad, fechas, validación, limpieza, carga, errores y ausencia de datos.
- `Alertas.test.jsx`: tarjetas, orden, filtros, páginas, reinicio, final vacío,
  justificación, pesos, errores y ausencia de estados ficticios.
- `App.test.jsx`: propagación de enfermedad y restricciones de roles.
- Build de producción correcto: 75 módulos transformados, salida en `dist/`.
- `git diff --check`: sin errores.
- No hay script ni configuración de lint en este frontend; no se agregó uno.

Vitest y Testing Library utilizan respuestas simuladas únicamente dentro de
tests, identificadas como fixtures. No se ejecutaron seeds ni se tocó `.env`.

### Extensión de vigencia para planificación (TASK-030)

El servidor reutiliza la selección existente de la última predicción por
municipio y enfermedad, considerando todas las predicciones, sin filtrar por
horizonte, alerta o fecha antes de determinar cuál es la última. El desempate
es por ID descendente. Una nueva predicción sin alerta invalida la anterior.
Después exige fecha objetivo >= hoy UTC, justificación con contenido y una
lista no vacía de explicaciones: todas con variable de texto no vacía y peso
numérico (incluidos cero y negativos). El filtro se aplica antes de paginar.
No representa un criterio epidemiológico ni un flujo de atención o resolución.
No cambia el comportamiento del parámetro omitido o `false`.

Se ejecutaron **18 pruebas de integración aprobadas, 0 fallidas y 0 omitidas**
en `tests/alertas_vigentes/test_alertas_vigentes.py`, con PostgreSQL/PostGIS,
HTTP y JWT reales. Cubren sustitución, predicciones sin alerta, vencimiento,
hoy UTC, explicaciones inválidas, paginación, compatibilidad y roles existentes.
Solo se utilizaron fixtures transaccionales revertidas en el contenedor
exclusivo `gatobyte-task024025-test`; no se usó la base del `.env`, ni seeds,
migraciones o cambios persistentes de datos.

Con `GATOBYTE_TEST_DATABASE_URL` apuntando a esa base exclusiva ya migrada,
desde `dengue-malaria-prediccion/`:

```powershell
../.venv/Scripts/python.exe -B -m unittest discover -s tests/alertas_vigentes -v
```

La suite rechaza otras bases. Sin URL o dependencias se omite explícitamente.
La extensión requiere PostgreSQL con JSONPath (probada en PostgreSQL 16).
La respuesta agrega `fecha_estimada_riesgo`; no cambia campos anteriores,
modelos ORM, migraciones, generación de alertas ni permisos. Se reutiliza
`app.services.predicciones._vigentes`; cambios futuros a ese helper requieren
ejecutar también esta suite. El contrato aún no informa el total de resultados.

## Límites pendientes de datos reales

Para la defensa se necesitan usuarios autorizados, predicciones históricas,
brotes confirmados con fuente legítima y alertas realmente generadas por
TASK-015. No se fabrican esos registros en producción. TASK-015 existe en
el código actual; algunas notas antiguas del backlog aún la describen pendiente.

La disponibilidad de esos datos condiciona la demostración funcional con
información real, no la implementación de filtros, tablas o paginación.
Mostrar una coincidencia o una justificación no acredita eficacia sanitaria
ni validación predictiva fuera de muestra.
