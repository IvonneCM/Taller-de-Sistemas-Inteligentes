# Product Goal: Soluciones de IA para Salud y Ayuda Social

Elige el enunciado que corresponda al caso seleccionado.

---

## **OPCIÓN A: Triaje Inteligente para Emergencias Saturadas**

### Enunciado

Para **médicos y enfermeras de emergencia en hospitales públicos**, construiremos un **sistema que clasifica automáticamente la urgencia de pacientes** que permite **reducir el tiempo de atención a casos críticos de 2-3 horas a 15-20 minutos, evitando muertes prevenibles por retraso diagnóstico**, utilizando datos clínicos básicos (signos vitales, síntomas, historial) y despliegue en tablets de triaje.

---

### Verificación de calidad

| Criterio | Cumple | Evidencia |
|----------|--------|-----------|
| ¿Usuario real entiende para qué existe? | ✅ SÍ | "Médica en emergencia ve que el sistema la ayuda a saber quién atiende primero" |
| ¿Usuario identificado? | ✅ SÍ | Médicos/enfermeras de emergencia (CAJA, HCU, hospitales públicos) |
| ¿Problema específico? | ✅ SÍ | Colas desorganizadas, críticos esperan 2-3h, muertes evitables por espera |
| ¿Métrica de éxito? | ✅ SÍ | Reduce tiempo de atención a críticos en 80% |
| ¿Sin tecnología como fin? | ✅ SÍ | No menciona "ML" o "IA", solo resultado (reducir espera) |

### Contexto de éxito

- **Restricción principal:** Acceso a datos históricos del CAJA (sensibles, requiere acuerdo)
- **Métrica clave:** Tiempo de atención a críticos antes/después
- **Criterio de aceptación:** En 100 casos nuevos, el sistema clasifica ≥90% igual que médico senior
- **Riesgo identificado:** Sesgo en datos históricos (ciertos grupos sub-diagnosticados)

---

## **OPCIÓN B: Detección de Desnutrición Infantil por Imagen (RECOMENDADO)**

### Enunciado

Para **trabajadores sociales, promotoras de salud y ONGs en zonas rurales sin clínicos**, construiremos un **sistema que detecta automáticamente signos de desnutrición en fotografías de niños** que permite **hacer screening masivo desde cualquier lugar con teléfono, identificando niños severos para derivación temprana a centros de referencia**, utilizando fotografías y conexión a redes de ayuda social (WhatsApp, SMS).

---

### Verificación de calidad

| Criterio | Cumple | Evidencia |
|----------|--------|-----------|
| ¿Usuario real entiende para qué existe? | ✅ SÍ | "Promotora toma foto de niño en comunidad remota, app dice si está desnutrido, conecta con trabajador social" |
| ¿Usuario identificado? | ✅ SÍ | Promotoras de salud, trabajadores sociales, ONGs (UNICEF, Save the Children, SEDES) |
| ¿Problema específico? | ✅ SÍ | 27% desnutrición infantil en Bolivia; 500k+ niños en zonas sin acceso a diagnóstico clínico |
| ¿Métrica de éxito? | ✅ SÍ | Detecta desnutrición severa con ≥85% precisión; agiliza referencia de 2-4 semanas a 24-48h |
| ¿Sin tecnología como fin? | ✅ SÍ | No menciona "computer vision"; resultado es "detectar niños en riesgo" |

### Contexto de éxito

- **Restricción principal:** Acceso a fotografías etiquetadas de ONGs/SEDES (baja fricción regulatoria)
- **Métrica clave:** Precisión de detección en distintos grupos étnicos/zonas geográficas
- **Criterio de aceptación:** En 50 niños de validación, modelo coincide con diagnóstico clínico en ≥85%
- **Riesgo identificado:** Variabilidad de fotografía (ángulo, iluminación); sesgo por etnia/geografía

### Escalabilidad

- App offline en smartphone (sin internet)
- Cualquier promotora, sin entrenamiento médico
- Funciona en cualquier zona rural de Bolivia
- Integración con sistema de alertas WhatsApp/SMS a trabajador social

---

## **OPCIÓN C: Predicción de Riesgo en Embarazo**

### Enunciado

Para **médicas de zona rural y enfermeras de centros de salud periféricos**, construiremos un **sistema que predice riesgo de complicaciones graves en embarazo (preeclampsia, parto prematuro)** que permite **derivar tempranamente a centros de maternidad especializados, evitando muertes maternas prevenibles**, utilizando datos clínicos básicos (presión arterial, proteinuria, hemoglobina, edad, antecedentes) y alertas para derivación inmediata.

---

### Verificación de calidad

| Criterio | Cumple | Evidencia |
|----------|--------|-----------|
| ¿Usuario real entiende para qué existe? | ✅ SÍ | "Médica en zona remota ve que embarazada tiene riesgo alto, la deriva a HCU sin demora, evita que muera" |
| ¿Usuario identificado? | ✅ SÍ | Médicas rurales, enfermeras de centros de salud periféricos (SEDES, zona rural boliviana) |
| ¿Problema específico? | ✅ SÍ | Bolivia: mortalidad materna 155/100k (vs 5/100k Chile); muchas muertes en zona rural por no detectar preeclampsia |
| ¿Métrica de éxito? | ✅ SÍ | Reduce mortalidad materna por preeclampsia no diagnosticada en 60%+ |
| ¿Sin tecnología como fin? | ✅ SÍ | No menciona "scoring"; resultado es "derivar a tiempo" |

### Contexto de éxito

- **Restricción principal:** Acceso a datos de embarazo (muy sensibles, requiere IRB/aprobación ética)
- **Métrica clave:** Sensibilidad en detectar preeclampsia ≥90%; especificidad ≥70%
- **Criterio de aceptación:** En cohorte de validación, modelo predice riesgo ≥2 semanas antes de evento clínico
- **Riesgo identificado:** Datos incompletos (no todas embarazadas tiene laboratorios); sesgo por acceso desigual a healthcare

### Escalabilidad

- Tablet en centro de salud rural
- Validación: Comparar predicciones con evolución real en zona piloto
- Integración con base de referencia regional (HCU, CAJA)
- Transferible a todas las zonas rurales de Bolivia

---

## Recomendación Final

✅ **Usar: OPCIÓN B (Desnutrición)**

**Razones:**
1. Máximo impacto social con mínima fricción regulatoria
2. Datos más accesibles (ONGs cooperan más que hospitales)
3. MVP más rápido (10-12 vs 14 semanas)
4. Escalabilidad nacional inmediata (app offline)
5. Innovación comprobada (no existe en Bolivia)

Si se abre acceso a datos del CAJA en mes 2 → pivotar a A.  
Si se completa B y queda tiempo → hacer C en semestre 2.

---

**Redactado por:** Equipo TSI  
**Fecha:** 13 de agosto del 2026
