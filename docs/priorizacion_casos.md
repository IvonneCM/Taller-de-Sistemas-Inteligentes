# Priorización de Casos: Soluciones de IA para Salud y Ayuda Social en Bolivia

## Objetivo
Comparar 3 propuestas innovadoras de machine learning para emergencias sanitarias y poblaciones vulnerables. Seleccionar la más viable para 18 semanas que maximize impacto en vidas y viabilidad técnica.

---

## Matriz de Evaluación

| Caso | Valor | Datos | Factibilidad | Riesgo | Despliegue | **Total** | Decisión |
|------|-------|-------|--------------|--------|-----------|----------|----------|
| **A. Triaje Inteligente en Emergencias** | 5 | 3 | 4 | 3 | 4 | **19** | Elegir |
| **B. Detección de Desnutrición Infantil** | 5 | 4 | 4 | 4 | 5 | **22** | Reserva prioritaria |
| **C. Predicción de Riesgo en Embarazo** | 5 | 3 | 4 | 4 | 4 | **20** | Reserva |

---

## Detalles de Evaluación

### **CASO A: Triaje Inteligente para Emergencias Saturadas**

**Valor (5/5):** Urgencia crítica
- Bolivia: ~50% de muertes prevenibles en emergencias por retraso diagnóstico
- Beneficiarios directos: CAJA, HCU, hospitales públicos con 300-500 pacientes/día
- Impacto: Reduce tiempo de atención a críticos de 2-3h a 15-20 min
- Usuario claro: Médicos de emergencia, enfermeras de triaje

**Datos (3/5):** Requiere acuerdos
- Requiere: Históricos de pacientes (3-5 años) del CAJA/HCU con triage + evolución
- Desafío: Datos sensibles (HIPAA-like), requiere aprobación ética
- Solución: Anonimización + acuerdo institucional con CAJA
- Riesgo: Puede tomar 4-6 semanas conseguir autorización

**Factibilidad (4/5):** Alcance controlable
- MVP viable en 8-10 semanas con 500-1000 casos históricos
- Stack: Gradient Boosting (XGBoost/LightGBM) es estándar
- Complejidad: Media (clasificación + scoring)
- Desafío: Validación clínica antes de despliegue

**Riesgo (3/5):** Moderado-alto
- Principal: Sesgo en datos históricos (ej: ciertas poblaciones sub-diagnosticadas)
- Regulatorio: Requiere validación clínica antes de usarse en vivo
- Técnico: Desbalance de clases (muchos "no urgentes" vs pocos "críticos")
- Solución: Validación cruzada + revisión clínica antes de producción

**Despliegue (4/5):** Implementable pero requiere capacitación
- Hardware: Laptop/tablet en triaje
- Personal: Requiere capacitación de enfermeras (1-2 semanas)
- Integración: Requiere conexión con sistema HCIS (si existe)
- Escalabilidad: Replicable a otras emergencias del país

**Restricción Principal:** ACCESO A DATOS + VALIDACIÓN CLÍNICA

---

### **CASO B: Detección de Desnutrición Infantil por Imagen**

**Valor (5/5):** Urgencia crítica
- Bolivia: 27% de desnutrición crónica en menores de 5 años (ENDSA 2016)
- Beneficiarios: 500k+ niños en zonas rurales/periurbanas sin acceso a centros de salud
- Impacto: Screening masivo con fotografía de teléfono (cualquier lugar)
- Usuario claro: Trabajadores sociales, promotoras de salud, ONGs (UNICEF, Save the Children)

**Datos (4/5):** Relativamente accesibles
- Requiere: Base de fotos de niños + datos antropométricos (peso, altura, circunferencia braquial)
- Fuentes posibles: 
  - Proyectos de ONGs (UNICEF tiene registros)
  - SEDES de La Paz/Cochabamba
  - Estudios previos de desnutrición
- Solución: Sintetizar datos con ImageNet + ajuste fino
- Ventaja: Computer vision es aplicable directamente

**Factibilidad (4/5):** Alcance bien definido
- MVP viable en 10-12 semanas
- Stack: Transfer learning (ResNet-50 pretrained) es estándar
- Complejidad: Media-alta (CV)
- Datos necesarios: 300-500 fotos etiquetadas (leve/moderada/severa)

**Riesgo (4/5):** Bajo-moderado
- Principal: Variabilidad de fotografía (ángulo, iluminación, fondo)
- Solución: Augmentación de datos + estandarizar protocolo de foto
- Validación: Simples pruebas clínicas (compare modelo vs diagnóstico clínico real)
- Regulatorio: Bajo (no es diagnostico, es screening)

**Despliegue (5/5):** Extremadamente práctico
- Hardware: Cualquier smartphone (sin internet necesario)
- App descargable + modelo embebido (offline)
- Integración: Notifica a trabajador social vía WhatsApp/SMS
- Escalabilidad: Funciona en cualquier zona rural, nacional

**Restricción Principal:** ACCESO A FOTOS ETIQUETADAS (menor que A)

---

### **CASO C: Predicción de Riesgo en Embarazo (Preeclampsia, Parto Prematuro)**

**Valor (5/5):** Urgencia crítica
- Bolivia: Mortalidad materna 155/100k (vs 5/100k Chile, 12/100k Argentina)
- Beneficiarios: 300k+ embarazadas anuales en zonas rurales sin acceso a obstetricia
- Impacto: Derivación temprana salva vidas (preeclampsia mata si no se trata)
- Usuario claro: Médicas de zona, enfermeras, centros de salud periféricos

**Datos (3/5):** Requiere acuerdos + sensibles
- Requiere: Registros de embarazo (PA, proteinuria, hemoglobina, edad, antecedentes) + outcomes
- Fuentes: HCU, CAJA, centros de salud (datos sensibles)
- Desafío: Datos de embarazo son altamente sensibles (confidencialidad)
- Volumen: Necesita 1000+ casos históricos para entrenamiento robusto
- Solución: Anonimización rigurosa + IRB (Junta Ética)

**Factibilidad (4/5):** Alcance factible pero requiere recolección
- MVP viable en 12-14 semanas (incluye tiempo de datos)
- Stack: Gradient Boosting + time series (PA cambia en el embarazo)
- Complejidad: Media (scoring + alertas)
- Datos faltantes: Desafío real (no todas hacen laboratorios)

**Riesgo (4/5):** Moderado
- Principal: Datos incompletos (no todas embarazadas tienen lab)
- Regulatorio: Requiere aprobación ética (datos muy sensibles)
- Clínico: Modelos pueden tener sesgo por acceso a healthcare
- Solución: Impute missing + validación clínica rigurosa

**Despliegue (4/5):** Práctico pero requiere integración
- Hardware: Tablet/smartphone en centro de salud
- Integración: Conectar con base de datos local de SEDES
- Personal: Capacitación de médicas rurales (2-3 semanas)
- Escalabilidad: Replicable a todas las zonas rurales

**Restricción Principal:** DATOS SENSIBLES + APROBACIÓN ÉTICA

---

## Justificación de la Decisión

### **Se elige: CASO B (Desnutrición)**

**Por qué:**

1. **Máximo impacto con mínima fricción regulatoria**
   - No requiere permisos hospitalarios (puede entrenar con ONGs)
   - No es "diagnóstico" médico legal (es screening)
   - Alcanza poblaciones sin acceso a centros de salud

2. **Datos más accesibles**
   - ONGs como UNICEF/Save the Children tienen miles de fotos etiquetadas
   - Menos barreras legales que datos hospitalarios
   - Transfer learning funciona bien (solo necesita ajuste fino)

3. **MVP más rápido**
   - 10-12 semanas vs 12-14 de C
   - Menos dependencias de acuerdos institucionales

4. **Escalabilidad nacional inmediata**
   - App offline en smartphone = cualquier promotora de salud
   - No requiere infraestructura hospitalaria
   - Impacto potencial: 500k+ niños

5. **Innovación comprobada**
   - Computer vision para desnutrición no existe en Bolivia
   - Transferible a toda Latinoamérica

---

### **Reserva Prioritaria: CASO A (Triaje)**

**Por qué es alternativa viable:**
- Impacto crítico (salva vidas hoy en emergencias)
- Viabilidad técnica comprobada (hospitals globales lo usan)
- Desafío: Conseguir datos históricos del CAJA (4-6 semanas de negociación)

**Recomendación:** Paralelo a B, iniciar conversaciones con CAJA dirección para acceso a datos. Si se abre en mes 2, pivotar a A.

---

### **Reserva: CASO C (Embarazo)**

**Por qué es alternativa:**
- Impacto: Mortalidad materna es crisis real
- Desafío: Datos muy sensibles + requiere IRB + acuerdos hospitales
- Recomendación: Ejecutar después de B (semestre 2) cuando equipo tenga experiencia regulatoria

---

## Resumen Ejecutivo

| Métrica | Caso A | Caso B | Caso C |
|--------|--------|--------|--------|
| Puntuación | 19/25 | **22/25** ✅ | 20/25 |
| Impacto (vidas) | Crítico | **Crítico** | Crítico |
| Tiempo acuerdos | ⚠️ 4-6 sem | ✅ 1-2 sem | ⚠️ 6-8 sem |
| Viabilidad técnica | Alta | **Alta** | Alta |
| Escalabilidad | Alta | **Máxima** | Alta |
| Risk regulatorio | Moderado | **Bajo** | Alto |

---
