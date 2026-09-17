# Restricciones de privacidad y licencias de datos

**Autor:** Ignacio Retamozo

**Estado:** Propuesta para revisión del equipo

**Trazabilidad:** REQ-013, REQ-014, REQ-015, REQ-020, `design.md` §6,
`docs/eda_inicial.md`, `docs/inventario_datos.md`,
`docs/reglas_calidad_datos.md` (EPI-05), `docs/controles_seguridad.md`
(SEG-05), TASK-035

## 1. Objetivo y alcance

Este documento tiene dos propósitos:

1. **Confirmar explícitamente** que ninguna fuente de datos usada o
   considerada por el proyecto expone información personal de pacientes,
   conforme a REQ-020 y a la regla no negociable 2 de `CLAUDE.md`.
2. **Documentar las licencias o condiciones de uso** de cada fuente pública
   considerada en `docs/inventario_datos.md`, para dejar constancia de bajo
   qué términos el proyecto está autorizado a descargar, procesar y
   redistribuir (de forma agregada) estos datos.

Aplica a los datos ya presentes en el repositorio (Ministerio de Salud,
SENAMHI) y a las fuentes todavía candidatas (SEDES, SNIS, NASA POWER,
OPS/PAHO, INE), siguiendo las convenciones de estado ya definidas en
`docs/inventario_datos.md` §"Convenciones de estado".

Siguiendo la regla de evidencia del proyecto, toda afirmación sobre licencias
que no pudo verificarse en una fuente oficial se marca explícitamente como
**no confirmada** en vez de asumirse.

---

## 2. Confirmación de cumplimiento de REQ-020

### 2.1 Declaración

**Se confirma que, a la fecha de este documento, ninguna fuente de datos
usada por el proyecto (Ministerio de Salud y Deportes — Boletín
Epidemiológico N.º 13/2026; SENAMHI Bolivia — WIS 2.0) contiene ni expone
identificadores personales de pacientes** (nombre, carnet de identidad,
dirección exacta, historia clínica, teléfono, coordenadas del paciente o
equivalente). Todo dato epidemiológico presente en el repositorio está
agregado por `departamento`/`municipio` (o SEDES) y periodo epidemiológico;
todo dato climático corresponde a estaciones meteorológicas, no a personas.

Esta confirmación se basa en evidencia verificable (§2.2), no en una
suposición de diseño.

### 2.2 Evidencia revisada por archivo

Se inspeccionaron directamente las columnas de los archivos epidemiológicos
procesados en el repositorio:

| Archivo | Columnas | Unidad de agregación | Identificadores personales |
|---|---|---|---|
| `data/processed/dengue_municipal_validado.csv` | `departamento, municipio, anio, casos_dengue_acumulados_se1_13, incidencia_por_10000_hab, periodo, fuente, pagina_fuente, nota, estado_calidad, ...` | Municipio + periodo (SE1-13) | Ninguno |
| `data/processed/malaria_municipal_validado.csv` | `sedes_segun_tabla, municipio, anio, periodo, p_vivax, p_falciparum, mixta, total_malaria, fuente, pagina_fuente, nota, estado_calidad, ...` | Municipio/SEDES + periodo | Ninguno |
| `data/processed/dengue_semanal_validado.csv` | `anio, semana_epidemiologica, casos_dengue, fuente, pagina_fuente, nota, estado_calidad, ...` | Nacional + semana epidemiológica | Ninguno |
| `data/processed/clima_diario.csv`, `clima_semanal.csv`, `clima_diario_imputado.csv` | Variables climáticas por estación/municipio y fecha (temperatura, humedad, precipitación) | Estación meteorológica + fecha | No aplica (dato ambiental, no de personas) |

No se encontró en ninguno de estos archivos, ni en `data/raw/epidemiologia.dvc`
(cuyo contenido real está versionado por DVC y excluido de Git —
ver `docs/controles_seguridad.md` §2), columna alguna con nombre, CI,
dirección, teléfono o historia clínica de un paciente individual.

Los datos crudos originales (`dengue_bolivia_municipal_SE01_13_2026.csv`,
`dengue_bolivia_semanal_SE01_13_2026.csv`,
`malaria_bolivia_municipal_SE01_13_2026.csv`) provienen de un boletín
epidemiológico público que reporta **conteos agregados por
municipio/SEDES**, tal como lo indica `docs/eda_inicial.md` §2.1 y
`docs/inventario_datos.md` §2.1; la fuente oficial nunca entrega registros a
nivel de caso individual.

### 2.3 Reglas del pipeline que refuerzan REQ-020

- `docs/reglas_calidad_datos.md`, regla **EPI-05**: "Registro individual o
  con identificadores personales → Rechazar y no persistir, conforme a
  REQ-020." Esta regla es parte del contrato de calidad que deberá
  implementar TASK-010 (`app/etl/limpieza.py`).
- `docs/reglas_calidad_datos.md` §7: "El pipeline no debe continuar si [...]
  se detectan datos personales."
- `docs/controles_seguridad.md`, control **SEG-05** (Minimización de datos):
  "Persistir casos agregados por municipio, enfermedad y periodo" y §7
  ("Privacidad y datos epidemiológicos"): lista explícita de campos
  prohibidos y exige una lista permitida ("allow-list") de columnas en los
  conectores de ingesta.
- `design.md` §3 (modelo de datos): la tabla `casos_epidemiologicos` solo
  define `municipio_id`, `enfermedad_id`, `fecha_reporte`,
  `casos_confirmados`, `fuente`, `fecha_ingesta`, `es_dato_imputado` — no
  existe columna para identificar pacientes individuales.
- `.gitignore` excluye `data/raw/` de Git (los datos crudos viajan solo por
  DVC), reduciendo el riesgo de que un archivo crudo con formato distinto al
  esperado quede expuesto sin revisión.

### 2.4 Limitación de esta confirmación

Esta confirmación cubre las fuentes **ya integradas** al repositorio
(Ministerio de Salud, SENAMHI). Las fuentes todavía no descargadas (SEDES,
SNIS, NASA POWER, INE — ver §3) deberán pasar por la misma verificación de
columnas antes de integrarse, y su conector deberá implementar la regla
EPI-05 desde el primer commit que las incorpore. Ninguna fuente pendiente
debe darse por conforme a REQ-020 hasta repetir esta revisión con sus datos
reales.

---

## 3. Licencias y condiciones de uso por fuente pública considerada

Para cada fuente se documenta: licencia/términos encontrados, si exige
atribución, si restringe uso comercial, y el estado de verificación. Cuando
no se localizó una licencia explícita para el dataset puntual usado por el
proyecto, se indica expresamente **"no confirmada"** en vez de asumir un
término favorable.

### 3.0 Marco general aplicable a entidades del Estado boliviano: DAT-002

Se localizó y **se leyó íntegramente** el documento oficial *"Términos y
condiciones de uso de datos abiertos"* (código **DAT-002**), elaborado por el
Consejo para las Tecnologías de Información y Comunicación del Estado
Plurinacional de Bolivia (CTIC-EPB), La Paz, 2019. Copia local conservada
para trazabilidad en
[`docs/fuentes_legales/DAT-002_terminos_condiciones_datos_abiertos_bolivia_2019.pdf`](fuentes_legales/DAT-002_terminos_condiciones_datos_abiertos_bolivia_2019.pdf).

Este documento **no es una licencia Creative Commons**, sino un marco
técnico-normativo propio del Estado boliviano, con el mismo efecto práctico:
define qué puede hacer un usuario con los datos abiertos publicados por
cualquier entidad del sector público, y bajo qué condiciones.

**Alcance (§5):** aplica a los datos abiertos publicados por **"cualquier
entidad publicadora del Estado"**, con dos excepciones explícitas (nota al
pie 4 del documento):

1. Información a la que **no se accedió mediante publicación o divulgación**
   de la propia entidad, sino en virtud de la legislación de acceso a la
   información (ej. una solicitud formal de información).
2. Derechos de terceros que la entidad publicadora no esté autorizada a
   otorgar.

**Definición de "dato abierto" (§3):** datos accesibles, estandarizados y
reutilizables que una entidad del sector público genera, administra o
custodia, y que pueden obtenerse **de forma libre y sin restricciones**. La
definición de "entidad publicadora" no exige que el dato haya sido generado
originalmente con fines de difusión estadística — basta con que la entidad lo
publique bajo lineamientos de datos abiertos.

**Qué permite (§7 y §9 — "Declaración de uso de datos abiertos del Estado
Plurinacional de Bolivia"):**

1. Procesar los datos abiertos (adaptar, combinar, extraer, compilar,
   transformar, derivar).
2. Distribuir, redistribuir, publicar o difundir los datos abiertos o los
   productos de su procesamiento.

**Condiciones que exige (§8 y §9):**

1. Citar la fuente de origen de los datos y su URL (todas las fuentes usadas,
   si son varias).
2. Citar la fecha de actualización o publicación del conjunto de datos
   utilizado.
3. Mantener las mismas libertades y condiciones de esta declaración en el
   procesamiento y publicación resultante (cláusula tipo *share-alike*).
4. (Recomendado, no obligatorio) documentar la metodología del
   procesamiento.

**Exclusión de responsabilidad (§8.1):** la entidad publicadora no responde
por el procesamiento que haga el usuario ni por daños derivados; el uso de
los datos **no implica aval, patrocinio ni respaldo** de la entidad de
origen; y los resultados del procesamiento del usuario **no se consideran
datos oficiales** de la entidad publicadora.

Este marco es la base legal más concreta y verificable encontrada para
evaluar las fuentes bolivianas del proyecto (§3.1, §3.2, §3.5), y reemplaza
la referencia indirecta a "CC BY-SA 4.0 / ODbL" citada en una versión previa
de este documento a partir de una descripción de segunda mano de
`datos.gob.bo`; esa referencia se mantiene solo como dato adicional en la
matriz de §4, no como la fuente primaria de esta sección.

### 3.1 Ministerio de Salud y Deportes de Bolivia — Boletín Epidemiológico N.º 13, 2026

| Campo | Detalle |
|---|---|
| **Tipo de fuente** | Publicación pública directa de una entidad del Estado Plurinacional de Bolivia (`minsalud.gob.bo`) |
| **Forma de acceso usada** | Descarga directa del boletín público (PDF) desde el sitio oficial del Ministerio, sin registro, sin pago y sin solicitud formal previa |
| **Licencia aplicable — confirmada** | **DAT-002** (§3.0). El boletín se obtuvo mediante publicación/divulgación directa del propio Ministerio en su sitio oficial, por lo que **no aplica la excepción (i)** del §5 de DAT-002 (esa excepción cubre datos obtenidos por solicitud de información, no publicaciones abiertas del propio sitio). El Ministerio también figura como entidad publicadora activa en el portal nacional `datos.gob.bo`, lo que refuerza su adhesión al régimen de datos abiertos del Estado. |
| **Condiciones que el proyecto debe cumplir** | (1) Citar fuente + URL — **cumplido parcialmente**: las columnas `fuente` y `pagina_fuente` ya citan la institución y el número de página del boletín (ver `dengue_municipal_validado.csv`), pero **falta registrar la URL exacta de descarga** del boletín N.º 13/2026 en la documentación del proyecto. (2) Citar fecha de publicación del boletín — **pendiente**: el pipeline registra `fecha_ingesta` (cuándo el sistema recibió el dato), no la fecha de publicación oficial del boletín; deben ser campos distintos. (3) Mantener las mismas libertades en obras derivadas (predicciones, dashboard) — a decidir por el equipo antes de publicar el sistema fuera del entorno académico. |
| **Uso que hace el proyecto** | Extracción de conteos agregados por municipio/SEDES y periodo epidemiológico; ningún dato de paciente individual (ver §2). |
| **Recomendación** | Completar la URL exacta y la fecha de publicación del boletín en la trazabilidad del dataset (TASK-009), y asegurar que el dashboard no dé a entender patrocinio o aval del Ministerio (§8.1 de DAT-002). |

### 3.2 SENAMHI Bolivia — WIS 2.0 (`wis.senamhi.gob.bo`)

| Campo | Detalle |
|---|---|
| **Tipo de fuente** | API pública (OGC API - Features) de una entidad técnico-científica descentralizada del Estado (`senamhi.gob.bo`) |
| **Forma de acceso usada** | Descarga automatizada vía `scripts/descargar_senamhi.py` contra el endpoint público `https://wis.senamhi.gob.bo/oapi/collections/...`, sin autenticación ni credenciales visibles en el script |
| **Licencia aplicable — confirmada con una salvedad** | **DAT-002** (§3.0) aplicaría por el mismo razonamiento que en §3.1: es un servicio publicado directamente por una entidad descentralizada del Estado, accesible libremente y sin restricción aparente (sin login, sin clave de API), lo que encaja en la definición de "dato abierto" del §3 de DAT-002. **Salvedad:** DAT-002 no fue redactado pensando en APIs de estaciones meteorológicas específicamente, y no se localizó una página propia de SENAMHI que invoque explícitamente este marco (a diferencia del Ministerio de Salud, que sí aparece en `datos.gob.bo`). Se trata por tanto de una aplicación razonable del marco general, no de una confirmación literal por parte de SENAMHI. |
| **Condiciones que el proyecto debe cumplir** | Igual que en §3.1: citar fuente + URL del endpoint (ya documentado en `scripts/descargar_senamhi.py` y `docs/eda_inicial.md` §2.2), citar la fecha/periodo de los datos descargados (ya cubierto: 14-ene-2026 a 4-abr-2026, ver `docs/eda_inicial.md` §2.2), y no dar a entender aval de SENAMHI sobre las predicciones del sistema. |
| **Uso que hace el proyecto** | Datos meteorológicos (temperatura, humedad, precipitación) por estación/municipio, sin ninguna relación con personas. Control de calidad y trazabilidad de la descarga documentados en `docs/eda_inicial.md` §4. |
| **Nota de coherencia interna** | `docs/inventario_datos.md` §3.1 marca a SENAMHI como **"Pendiente de completar (requiere validación del equipo)"**, mientras que `design.md` §10 y `CONTEXT.md` la dan como **"fuente climática confirmada"** tras el EDA de la sesión 2026-09-16. Esta discrepancia de estado sigue sin resolverse en `docs/inventario_datos.md`; este documento no la corrige, solo la señala, porque el estado de acceso (confirmada vs. pendiente) es distinto del estado de licencia que se documenta aquí. |
| **Recomendación** | Confirmar con SENAMHI (o la ONDHI/INADHI) si existe una página de términos propia para WIS 2.0; mientras tanto, tratar DAT-002 como base razonable pero no como confirmación literal de la entidad. |

### 3.3 NASA POWER (alternativa climática — pregunta abierta, no usada actualmente)

| Campo | Detalle |
|---|---|
| **Tipo de fuente** | API pública de la NASA (Prediction of Worldwide Energy Resources) |
| **Estado de uso en el proyecto** | No usada; listada como alternativa en `docs/inventario_datos.md` §3.2 ("Pregunta abierta") |
| **Licencia confirmada** | **Sí.** NASA POWER declara explícitamente que no existen restricciones de uso, acceso o descarga de sus datos, y los distribuye bajo **Creative Commons Attribution 4.0 (CC BY 4.0)**. |
| **Atribución requerida** | Sí — NASA solicita una cita/agradecimiento estándar al usar los datos en una publicación (ver `power.larc.nasa.gov`). |
| **Restricción comercial** | Ninguna. |
| **Recomendación** | Si el equipo decide activarla como fuente climática adicional o de respaldo, solo resta agregar la cita sugerida por NASA en la documentación de la fuente; no se requiere gestión adicional de licencia. |

### 3.4 OPS/PAHO — validación regional (`opendata.paho.org`)

| Campo | Detalle |
|---|---|
| **Tipo de fuente** | Portal de datos abiertos de la Organización Panamericana de la Salud |
| **Estado de uso en el proyecto** | "Acordada (pública)" en `docs/inventario_datos.md` §3.3, para validación regional, no como fuente primaria |
| **Licencia confirmada** | **Sí, con restricción.** El portal declara licencia **Creative Commons BY-NC 3.0 IGO** por defecto ("except when indicated otherwise"), lo que exige atribución y **prohíbe el uso comercial**. |
| **Compatibilidad con el proyecto** | Compatible, porque el proyecto es un piloto universitario sin fines comerciales. **Si el sistema se despliega alguna vez en un contexto comercial o de prestación de servicios pagados, esta fuente debería revisarse** (algunos recursos individuales del portal pueden tener licencias distintas, según el propio portal). |
| **Recomendación** | Verificar la licencia del recurso puntual descargado (no solo la licencia general del portal) antes de citarlo, y mantener la atribución a OPS/PAHO en cualquier reporte que use estos datos de validación. |

### 3.5 INE — Instituto Nacional de Estadística de Bolivia

| Campo | Detalle |
|---|---|
| **Tipo de fuente** | Entidad pública boliviana, datos poblacionales/geográficos (censos, Redatam) |
| **Estado de uso en el proyecto** | "Pendiente de completar" en `docs/inventario_datos.md` §4.1; no se ha decidido si se incorpora |
| **Licencia explícita localizada** | El sitio institucional (`ine.gob.bo`) enlaza a una página de "Licencia de uso" propia, cuyo contenido no pudo verificarse con las herramientas de esta revisión (no se descargó un PDF equivalente al de §3.0). |
| **Marco general aplicable** | El INE figura como organización publicadora en `datos.gob.bo` y, si sus datasets se descargan directamente de su publicación oficial (no vía solicitud de información), aplicaría el mismo marco **DAT-002** de §3.0. Esto no está confirmado para todos sus productos: los microdatos censales vía Redatam suelen requerir aceptar condiciones de acceso propias (registro, finalidad declarada) que pueden ser más restrictivas que DAT-002, ya que Redatam no siempre se distribuye como descarga abierta directa. |
| **Recomendación** | Antes de incorporar población o límites municipales del INE (necesario para `municipios.poblacion_estimada` y la geometría PostGIS), revisar la página `/licencia` del INE y, si se usan microdatos vía Redatam, confirmar sus condiciones específicas de acceso (pueden no equivaler a una descarga abierta directa). |

### 3.6 SEDES (Servicio Departamental de Salud) — pendiente de solicitud

| Campo | Detalle |
|---|---|
| **Estado de uso en el proyecto** | "Acordada (pendiente de descarga)" en `docs/inventario_datos.md` §2.2; requiere solicitud formal por correo a `epidemiologia@sedes.lapaz.gob.bo` |
| **Licencia** | **DAT-002 (§3.0) probablemente NO aplica a esta fuente**, y esto es una diferencia importante respecto a §3.1/§3.2: la vía de acceso descrita es una **solicitud formal de información**, no una publicación/divulgación abierta del propio SEDES. Esto corresponde exactamente a la excepción (i) del §5 de DAT-002 ("información a la que no se ha accedido mediante publicación o divulgación de la entidad publicadora, en virtud de la legislación sobre acceso a la información"). |
| **Consecuencia práctica** | Los términos de reutilización de los datos de SEDES **deberán confirmarse en la respuesta formal** que envíe la institución (o en cualquier condición que adjunten a la entrega), y no pueden asumirse automáticamente bajo el marco general de datos abiertos del Estado. Además, deberá verificarse que el formato de entrega siga siendo agregado por zona/semana y no por caso individual (reforzar EPI-05 en el momento de la integración). |

### 3.7 SNIS (Sistema Nacional de Información en Salud)

| Campo | Detalle |
|---|---|
| **Estado de uso en el proyecto** | "Pregunta abierta" en `docs/inventario_datos.md` §2.3; fuente aún no definida |
| **Licencia** | No aplica todavía — no hay fuente de acceso identificada. |

---

## 4. Matriz resumen de licencias

| # | Fuente | Estado de uso | Licencia | Atribución requerida | Uso comercial permitido | Share-alike / misma licencia en derivados |
|---|---|---|---|---|---|---|
| 3.1 | Ministerio de Salud (Boletín N°13) | Confirmada (datos en repo) | **DAT-002** (Estado boliviano) — confirmada por texto primario | Sí, + fecha de publicación (falta completar) | Sí, sin fin de lucro implícito en la definición; no revisado para uso comercial explícito | Sí (condición 3 de DAT-002) |
| 3.2 | SENAMHI (WIS 2.0) | Confirmada en `design.md`/`CONTEXT.md`, pero "pendiente" en `inventario_datos.md` (discrepancia sin resolver) | **DAT-002** aplicable por razonamiento (no confirmado literalmente por SENAMHI) | Sí | Igual que 3.1 | Sí (si aplica DAT-002) |
| 3.3 | NASA POWER | No usada (alternativa) | **CC BY 4.0** (confirmada) | Sí | Sí | No exige |
| 3.4 | OPS/PAHO | Acordada (validación) | **CC BY-NC 3.0 IGO** (confirmada) | Sí | **No** | No exige (pero no permite comercial) |
| 3.5 | INE | Pendiente de completar | **DAT-002** probable para datasets publicados directamente; Redatam puede tener condiciones propias no verificadas | Sí (si aplica DAT-002) | Depende del producto (censo vs. dataset agregado) | Sí (si aplica DAT-002) |
| 3.6 | SEDES | Acordada (pendiente de descarga) | **DAT-002 probablemente NO aplica** (acceso por solicitud formal, no por publicación abierta — excepción i del §5) | Por confirmar en la respuesta de SEDES | Por confirmar | Por confirmar |
| 3.7 | SNIS | Pregunta abierta | No aplica todavía | — | — | — |

---

## 5. Riesgos y vacíos pendientes

1. **Discrepancia de estado sobre SENAMHI** entre `docs/inventario_datos.md`
   (§3.1, "pendiente de completar") y `design.md`/`CONTEXT.md` ("fuente
   climática confirmada"). No afecta la aplicabilidad de DAT-002 (que
   depende de la forma de acceso, ya confirmada como descarga abierta vía
   API), pero sigue siendo una inconsistencia documental que el equipo debe
   resolver.
2. **DAT-002 se aplica a Ministerio de Salud y SENAMHI por análisis propio
   de este documento** (ambas son entidades del Estado que publican los
   datos directamente, sin solicitud previa), **no porque cada entidad haya
   confirmado explícitamente que se acoge a DAT-002**. Es la base legal más
   sólida disponible, pero sigue sin ser una confirmación literal
   entidad-por-entidad.
3. **Faltan dos campos de trazabilidad que exige DAT-002 y que el proyecto
   aún no captura de forma explícita**: la URL exacta de origen de cada
   fuente y la fecha de publicación/actualización del conjunto de datos
   (distinta de `fecha_ingesta`, que es cuándo el sistema recibió el dato,
   no cuándo la fuente lo publicó). Recomendado incorporarlos en TASK-008 y
   TASK-009.
4. **La condición de "share-alike" de DAT-002** (mantener las mismas
   libertades en la publicación resultante) implica que, si el proyecto
   publica el dashboard o los datos derivados fuera del entorno académico,
   debería ofrecerlos también en condiciones abiertas equivalentes. Esto no
   bloquea el piloto universitario, pero es una decisión de licenciamiento
   propio que el equipo debe tomar antes de un despliegue público.
5. **OPS/PAHO impone explícitamente una restricción de uso no comercial**
   (CC BY-NC 3.0 IGO). Es compatible con el alcance actual (piloto
   universitario) pero bloquea cualquier explotación comercial futura del
   sistema si se sigue usando esta fuente sin renegociar licencia.
6. **SEDES**: a diferencia de Ministerio de Salud y SENAMHI, su vía de
   acceso (solicitud formal por correo) cae en la excepción (i) del §5 de
   DAT-002, por lo que **no debe asumirse que sus datos quedarán bajo el
   mismo marco abierto**; los términos deberán confirmarse en la respuesta
   de la institución. **SNIS** sigue sin fuente ni licencia definida.
7. Ninguna de las fuentes revisadas está certificada por una autoridad
   externa como "libre de datos personales"; la confirmación de §2 se basa
   en inspección directa de las columnas disponibles en el repositorio, no
   en una garantía contractual de la fuente. Si una fuente futura cambia su
   formato de entrega (ej. SEDES entrega un Excel con más columnas de las
   esperadas), debe repetirse la revisión de §2 antes de integrarla.

---

## 6. Checklist de cumplimiento (insumo para TASK-035)

- [x] Se revisaron las columnas reales de los archivos epidemiológicos
      procesados en el repositorio y no se encontraron identificadores
      personales de pacientes (§2.2).
- [x] Se confirma que los datos climáticos (SENAMHI) no contienen
      información de personas (§2.2).
- [x] Se documentaron las reglas del pipeline (EPI-05, SEG-05) que impiden
      persistir datos personales si aparecieran en una fuente futura (§2.3).
- [x] Se documentó la licencia o su ausencia para cada fuente pública
      considerada en `docs/inventario_datos.md` (§3).
- [x] Se identificó y leyó el marco legal boliviano aplicable a datos
      abiertos de entidades del Estado (**DAT-002**, CTIC-EPB 2019) y se
      aplicó a Ministerio de Salud y SENAMHI (§3.0-§3.2).
- [ ] Registrar la URL exacta de origen y la fecha de publicación (no de
      ingesta) del boletín del Ministerio de Salud y de la descarga de
      SENAMHI, para cumplir las condiciones 1 y 2 de DAT-002 (§5.3).
- [ ] Confirmación por escrito de licencia con el Ministerio de Salud y
      Deportes, si el proyecto se despliega más allá del piloto académico
      (pendiente — recomendación en §3.1).
- [ ] Confirmación por escrito de licencia/términos de uso con SENAMHI,
      dado que DAT-002 se aplica por análisis propio y no por confirmación
      literal de la entidad (pendiente — recomendación en §3.2).
- [ ] Resolver la discrepancia de estado de SENAMHI entre
      `docs/inventario_datos.md` y `design.md`/`CONTEXT.md` (§5.1).
- [ ] Decidir si los datos/derivados del proyecto se publicarán bajo
      condiciones abiertas equivalentes (cláusula share-alike de DAT-002),
      antes de cualquier despliegue público (§5.4).
- [ ] Repetir esta revisión cuando se integren SEDES, SNIS o INE con datos
      reales, considerando que SEDES probablemente **no** queda cubierta por
      DAT-002 por tratarse de una solicitud formal, no de una publicación
      abierta (§2.4, §3.6, §5.6).

---

## 7. Referencias

- `requirements.md` — REQ-013, REQ-014, REQ-015, REQ-020
- `design.md` §3 (modelo de datos), §6 (seguridad)
- `CLAUDE.md` — regla no negociable 2 (no incluir datos personales de
  pacientes)
- `docs/eda_inicial.md` §2 (fuentes de datos), §4 (control de calidad)
- `docs/inventario_datos.md` (estado y forma de acceso de cada fuente)
- `docs/reglas_calidad_datos.md` — regla EPI-05, §7
- `docs/controles_seguridad.md` — control SEG-05, §7
- `docs/cierre_sprint1.md` (asignación de esta tarea al backlog de Data)
- **Fuente primaria leída íntegramente:** *"Términos y condiciones de uso de
  datos abiertos"* (DAT-002), Consejo para las Tecnologías de Información y
  Comunicación del Estado Plurinacional de Bolivia (CTIC-EPB), La Paz, 2019.
  Copia local:
  [`docs/fuentes_legales/DAT-002_terminos_condiciones_datos_abiertos_bolivia_2019.pdf`](fuentes_legales/DAT-002_terminos_condiciones_datos_abiertos_bolivia_2019.pdf).
- Otras fuentes externas consultadas (vía búsqueda web, sin descarga del
  documento primario): `minsalud.gob.bo`, `senamhi.gob.bo`, `datos.gob.bo`,
  `power.larc.nasa.gov`, `opendata.paho.org`, `ine.gob.bo`.
