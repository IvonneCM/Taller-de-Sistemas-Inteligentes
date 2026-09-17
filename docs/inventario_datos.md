# Inventario de fuentes de datos — Predicción de brotes de dengue/malaria (Bolivia)

**Sección del backlog:** Data
**Documentos relacionados:** `priorizacion_casos.md`, `product_goal.md`, `design.md` §10, `requirements.md` (REQ-013, REQ-014, REQ-015)

---

## 1. Objetivo de este inventario

Listar cada fuente de datos candidata del proyecto SIPTB con su **forma de
acceso**, su **estado de confirmación** (confirmada / acordada / pregunta
abierta / pendiente de completar) y su relación con los requisitos. Las
fuentes aún no confirmadas se marcan explícitamente como **referenciales**,
siguiendo la regla de evidencia del proyecto (no inventar datos no
verificados).

### Convenciones de estado

| Estado | Significado |
|---|---|
| **Confirmada** | Acceso validado y datos ya presentes en el repositorio. |
| **Acordada (pendiente de descarga)** | Fuente y forma de acceso identificadas, pero los datos aún no se han descargado. |
| **Pregunta abierta** | Fuente no definida todavía (ver `design.md` §10). |
| **Pendiente de completar** | Existe indicio de la fuente, pero falta información de acceso/confirmación para cerrarla. |

---

## 2. Fuentes de datos epidemiológicos

### 2.1 Ministerio de Salud y Deportes de Bolivia — Boletín Epidemiológico N°13, 2026

| Campo | Detalle |
|---|---|
| **Estado** | **Confirmada** (datos en el repositorio) |
| **Forma de acceso** | Descarga/extracción del boletín oficial; datos estructurados en CSV dentro del repo |
| **Ubicación en el repo** | `data/raw/epidemiologia/` |
| **Archivos** | `dengue_bolivia_semanal_SE01_13_2026.csv` (13 filas), `dengue_bolivia_municipal_SE01_13_2026.csv` (28 filas), `malaria_bolivia_municipal_SE01_13_2026.csv` (21 filas) |
| **Contenido** | Dengue: casos semanales nacionales y acumulados municipales SE 1-13. Malaria: `p_vivax`, `p_falciparum`, `mixta`, `total_malaria` por municipio/SEDES |
| **Cobertura** | Nacional; semanas epidemiológicas 1 a 13 de 2026 |
| **Formato** | CSV ya estructurado, con columnas de trazabilidad (`fuente`, `pagina_fuente`, `nota`) |
| **Calidad observada** | 0 valores faltantes y 0 duplicados (ver `scripts/eda_output/calidad_datos.csv`) |
| **Totales verificados** | Dengue SE 1-13: **341 casos** · Malaria SE 1-13: **1,615 casos** |
| **Requisitos** | REQ-013 (ingesta), REQ-015 (procedencia/fuente) |
| **Notas / limitaciones** | Datos **provisionales** sujetos a actualización (indicado en la columna `nota`). En dengue municipal no se reconstruyó la semana municipal cuando la posición de celdas vacías del PDF era ambigua. En malaria, el texto narrativo atribuye Ixiamas a La Paz pero la tabla lo muestra bajo Pando; se conserva la tabla y se documenta la inconsistencia. |

### 2.2 SEDES (Servicio Departamental de Salud) — casos de dengue/malaria

| Campo | Detalle |
|---|---|
| **Estado** | **Acordada (pendiente de descarga)** — requiere solicitud formal |
| **Forma de acceso** | Solicitud formal por correo a `epidemiologia@sedes.lapaz.gob.bo`; respuesta en 3-7 días hábiles |
| **Contenido** | Casos por zona/semana |
| **Volumen estimado (referencial)** | ~10k+ registros |
| **Formato** | Semi-estructurado (PDF → Excel); requiere paso de parseo |
| **Requisitos** | REQ-013, REQ-014 (nuevas fuentes sin rediseño) |
| **Notas** | Fuente referencial tomada de `priorizacion_casos.md:81`. La solicitud aún no está confirmada. El boletín del Ministerio (§2.1) es una fuente nacional complementaria, no equivalente al detalle por zona del SEDES. |

### 2.3 SNIS (Sistema Nacional de Información en Salud)

| Campo | Detalle |
|---|---|
| **Estado** | **Pregunta abierta** (`design.md` §10) |

---

## 3. Fuentes de datos climáticos

### 3.1 SENAMHI — Servicio Nacional de Meteorología e Hidrología

| Campo | Detalle |
|---|---|
| **Estado** | **Pendiente de completar** (requiere validación del equipo) |

### 3.2 NASA POWER (alternativa climática)

| Campo | Detalle |
|---|---|
| **Estado** | **Pregunta abierta** (`design.md` §10) |
### 3.3 OPS/PAHO — validación regional

| Campo | Detalle |
|---|---|
| **Estado** | **Acordada (pública)** |

---

---

## 5. Matriz resumen de estado

| # | Fuente | Tipo | Forma de acceso | Estado |
|---|---|---|---|---|
| 2.1 | Ministerio de Salud — Boletín N°13/2026 | Epidemiológico | Extracción oficial → CSV en repo | **Confirmada** |
| 2.2 | SEDES | Epidemiológico | Solicitud formal por correo | Acordada (pendiente) |
| 2.3 | SNIS | Epidemiológico | Por definir | Pregunta abierta |
| 3.1 | SENAMHI | Climático | Descarga web / correo | Pendiente de completar |
| 3.2 | NASA POWER | Climático | API pública | Pregunta abierta |
| 3.3 | OPS/PAHO | Epidemiológico (validación) | CSV descargable | Acordada (pública) |
| 4.1 | INE | Poblacional/geográfico | Por definir | Pendiente de completar |

---

## 6. Vacíos de información pendientes

1. **SENAMHI:** confirmar serie/estación exacta, resolución temporal, cobertura
   por municipio de la zona piloto y si se usa descarga web o solicitud formal.
2. **INE:** decidir si se incorpora y, de hacerlo, definir datasets exactos
   (población, límites municipales).
3. **SNIS:** confirmar si hay acceso a datos históricos para el piloto.
4. **SEDES:** enviar/confirmar la solicitud formal y verificar formato real de
   entrega.

---

## 7. Trazabilidad con requisitos

| Requisito | Fuentes involucradas |
|---|---|
| REQ-013 (ingesta de datos) | 2.1, 2.2, 3.1 |
| REQ-014 (nuevas fuentes sin rediseño) | 2.2, 2.3, 3.1, 3.2 |
| REQ-015 (procedencia/fuente + fecha de ingesta) | 2.1 (columnas `fuente`), 3.3 |

> **Nota de evidencia:** los volúmenes y accesos marcados como
> "referencial" provienen de `priorizacion_casos.md` y `design.md §10`; no
> deben citarse como confirmados hasta completar el acceso.
