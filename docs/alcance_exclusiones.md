# Alcance y exclusiones — SIPTB (resumen 1 slide)

**Responsable:** Ivonne Colque
**Sección del backlog:** Discovery
**Uso previsto:** diapositiva "Alcance" de la presentación
**Complementa:** `requirements.md` §6 y §6.1
**Estado de aprobación:** pendiente — revisar con el equipo antes de la presentación

---

## SÍ incluye (esta evaluación / MVP)

- Predicción temprana (3 a 4 semanas de anticipación) de riesgo de brote de
  **dengue y malaria** por municipio, orientada a autoridades de salud / SEDES /
  coordinadores municipales.
- Datos **reales** (no sintéticos): epidemiológicos (Ministerio de Salud,
  Boletín N.13, SE1-13 2026) + climáticos (SENAMHI WIS 2.0, 4 municipios).
- Pipeline reproducible de calidad: descarga, control de calidad, imputación,
  EDA y línea base.
- Línea base nacional como **referencia inicial** y protocolo de evaluación
  municipio-semana definido.
- Dashboard web con mapa de calor por zona/municipio/departamento, alertas con
  justificación, priorización de zonas para fumigación.
- Explicabilidad del modelo (variables que influyen), datos agregados y
  anonimizados (sin datos personales), RBAC y auditoría inmutable.

## NO incluye (fuera de alcance actual)

- Modelo predictivo municipal operativo (falta **serie temporal semana a semana**
  de casos por municipio); solo baseline nacional provisional como referencia.
- Datos históricos > 1 año (no hay estacionalidad ni mediana histórica).
- Zonas fuera de los 4 municipios con datos reales (resto de Bolivia queda en diseño).
- Integración en tiempo real con sistemas hospitalarios / historias clínicas;
  datos en streaming; app móvil nativa.
- Otras enfermedades (Zika, Chikungunya); notificaciones SMS/WhatsApp.
- Logística operativa de fumigación (solo prioriza zonas).
- Certificación oficial ante el Ministerio de Salud.
- Fuentes aún no confirmadas (SEDES, SNIS, NASA POWER, INE).

---

## Aprobación del equipo

- [ ] Revisado en reunión de equipo (fecha: ____)
- [ ] Sin observaciones / observaciones registradas: ______________________
- [ ] Aprobado para la presentación (nombre de quien aprueba: ____)