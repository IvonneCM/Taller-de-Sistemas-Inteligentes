# ADR-005: Malaria se guarda como acumulado en la base de datos (sin serie semanal inventada)

- **Estado:** Aceptado
- **Fecha:** 2026-10-25
- **Decisores:** Tania Pérez (capa de datos). Pendiente de comunicar al resto del equipo.
- **Relacionado:** `design.md` §3 y §10, `tasks.md` TASK-009, REQ-013, REQ-014, NFR-007, `docs/contrato_esquema_bd.md`, `docs/contrato_esquema_datos_procesados.md` §7bis, decisión 2 del reparto "Listo para Empezar"

## Contexto

La decisión 2 del reparto "Listo para Empezar" pide serie municipio-semana. Para
**dengue** existe: el Boletín N.º 13 trae casos por semana y municipio (SE1-13).
Para **malaria** no existe en ninguna fuente disponible: todos los boletines
revisados (SE5, 7, 8, 9, 13) entregan solo un acumulado SE1-k por municipio. SEDES
no ha respondido a la solicitud de datos semanales.

Restando acumulados de boletines consecutivos se reconstruyen **bloques** de semanas
(SE1-5, SE6-7, SE8, SE9, SE10-13); solo SE8 y SE9 son semanas individuales.
Los casos de malaria se reportan en tandas (p. ej. Ixiamas: 0 casos en SE6-8 y 20 en SE9),
así que repartir un bloque en partes iguales no refleja lo ocurrido.

De los 4 municipios piloto de la base, solo 3 tienen malaria (Guayaramerín, Ixiamas,
San Buenaventura): Palos Blancos no figura en la tabla de malaria.

## Alternativas consideradas

1. **A. Guardar solo el acumulado SE1-13** por municipio (como hoy).
2. **B. Repartir cada bloque entre sus semanas** con `es_dato_imputado = true`.
3. **C. Guardar los bloques tal cual**, agregando una columna `semanas_cubiertas`
   a `casos_epidemiologicos` (migración nueva).

## Decisión

**Opción A.** `casos_epidemiologicos` guarda para malaria una fila por municipio con el
acumulado SE1-13 (`fecha_reporte` = domingo de la SE13, `es_dato_imputado = false`).
No se estima, reparte ni interpola nada. Dengue sigue como serie semanal.

## Justificación

- No inventa datos (`CLAUDE.md`, regla 1): la base dice exactamente lo que dice el boletín.
- B habría marcado como estimadas ~85 % de las semanas y habría dado al modelo
  rezagos suavizados que no existen en la fuente (autocorrelación artificial que hace
  ver mejor al modelo de lo que es).
- C es más expresiva, pero cambia el esquema ya publicado y no resuelve el problema de
  fondo (sigue sin haber serie semanal de malaria); se puede retomar si llega
  información nueva.
- Ya está implementado y probado (`ingerir_epidemiologia_acumulada`).

## Consecuencias

- **Negativas / costos:**
  - La base tiene 3 filas de malaria (zona piloto): no hay rezagos semanales ni historial
    de malaria desde la BD. TASK-011 (rezagos), TASK-034 (validación retrospectiva) y las
    vistas de historial no pueden cubrir malaria con esta fuente.
  - Dengue y malaria quedan con granularidad distinta en la misma tabla: quien consuma
    `casos_epidemiologicos` debe filtrar por `fuente` y no sumar filas acumuladas con
    semanales de la misma enfermedad.
- **Mitigación para el modelo:** el modelo de malaria entrena con
  `data/processed/panel_bloques_malaria_clima.csv` (22 municipios, 101 bloques utilizables,
  con `casos_por_semana`), no con la base de datos. Ver `docs/guia_entrega_fase2.md`.
- **Limitación a declarar:** debe figurar en el informe final (TASK-036) y en el Risk
  Register (Fase 9): malaria no tiene serie semanal en la fuente.
- **Cuándo reabrir:** si SEDES/SNIS entrega casos semanales por municipio, bastaría
  ingerirlos como filas semanales (misma estructura que dengue); no requiere cambiar el
  esquema.
