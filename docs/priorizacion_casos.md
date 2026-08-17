# Priorización de Casos: Violencia de Género vs Dengue/Malaria
## LAB_01 - Taller de Sistemas Inteligentes

---

## Matriz de Evaluación

| Caso | Valor | Datos | Factibilidad | Riesgo | Despliegue | **Total** | Decisión |
|------|-------|-------|--------------|--------|-----------|----------|----------|
| **1. Detección Violencia Género** | 5 | 4 | 4 | 4 | 4 | **21** |  Reserva |
| **2 Predicción Dengue/Malaria** | 5 | 5 | 4 | 4 | 4 | **22** | Reserva |

---

## Detalles de Evaluación

### **CASO 1: Detección Automática de Violencia de Género en Llamadas**

**Valor (5/5):** Urgencia crítica
- Bolivia: Tasa de feminicidio 2.5 por 100k mujeres (ONU MUJERES)
- Beneficiarios directos: 500k+ mujeres en situación de violencia/año
- Impacto: Diferencia entre vida y muerte (derivación en minutos vs días)
- Usuario claro: Operadores líneas 100, CIPFE, Voces Amigas, SEDES
- Adicional: Transferible a cualquier línea de apoyo Latinoamérica

**Datos (5/5):** ACCESIBLES
- Fuente principal: Hugging Face (365k+ ejemplos públicos)
  - Wikipedia Toxic Comments: 160k+ textos
  - HASOC Dataset: 5k+ hate/abuse ejemplos anotados
  - Crisis Text Lines: 200k+ mensajes de crisis
- Acceso: Descarga directa (sin solicitud, sin espera)
- Formato: Estructurado, anotado profesionalmente
- Volumen: 365k+ ejemplos = robusto para training

**Alternativos públicos:**
- Kaggle datasets: gender-based violence transcripts (1-5k)
- GitHub repos: abuse-detection-NLP (10-50k)
- Zenodo: crisis conversations (500-2k)

**Factibilidad (4/5):** Alcance bien definido
- MVP viable en 10-12 semanas
- Stack: Whisper (speech-to-text) → spaCy (limpieza) → Transformers (clasificación)
- Complejidad: Media-alta (multimodal: audio + NLP)
- Desafío: Validación clínica con operadores reales

**Riesgo (4/5):** Bajo-moderado pero manejable
- Principal: Privacidad de víctimas (datos muy sensibles)
  - Solución: Usar datos públicos Hugging Face (ya anonimizados)
  - Respetar confidencialidad en deploy (encriptación)
- Técnico: Sesgo por etnia/acento en transcripción Whisper
  - Solución: Validar con múltiples acentos bolivianos
- Regulatorio: Bajo (datos públicos, no requiere IRB)

**Despliegue (4/5):** Práctico pero requiere capacitación
- Hardware: Servidor estándar (o cloud)
- Interfaz: Chatbot/app simple para operadores
- Integración: Alertas SMS/WhatsApp a coordinador
- Escalabilidad: Cualquier línea de apoyo, cualquier país
- Personal: Capacitación operadores 2-3 horas

**Restricción Principal:** PRIVACIDAD MÁXIMA (pero manejable con datos públicos)

---

### **CASO 2: Predicción de Brotes de Dengue/Malaria**

**Valor (5/5):** Urgencia crítica
- Bolivia: 100k+ casos dengue/año, muertes prevenibles
- Beneficiarios: 300k+ habitantes de zonas de riesgo
- Impacto: Prevención anticipada salva vidas
- Usuario claro: Médicos SEDES, coordinadores sanitarios, autoridades
- Alcance: Transferible a Perú, Colombia, Brasil (problema regional)

**Datos (4/5):** Accesibles pero requieren 1-2 acuerdos
- Fuente 1: SENAMHI (datos climáticos) — Fácil
  - URL: https://www.senamhi.gob.bo/sisop/
  - Acceso: Descarga web directo (30 min) o email 3-5 días
  - Volumen: 29k+ registros (temperatura, precipitación, humedad)
  - Formato: Limpio, validado

- Fuente 2: SEDES (casos dengue) — Requiere solicitud
  - Email: epidemiologia@sedes.lapaz.gob.bo
  - Acceso: Solicitud formal (3-7 días)
  - Volumen: 10k+ registros (casos por zona/semana)
  - Formato: Semi-estructurado (PDFs → Excel)

- Fuente 3: OPS/PAHO (validación regional) — Público
  - URL: https://www.paho.org/
  - Acceso: CSV descargable

**Volumen total esperado:** 40k+ registros (robusto)

**Factibilidad (4/5):** Alcance factible pero requiere limpieza
- MVP viable en 12-14 semanas
- Stack: Time series (Prophet/ARIMA) + geospatial (XGBoost) + LSTM
- Complejidad: Media-alta (spatial-temporal ML)
- Desafío: Datos incompletos (falta estaciones en zonas rurales); geocodificación inconsistente

**Riesgo (4/5):** Moderado
- Principal: Datos con gaps (no todas zonas tienen estación)
  - Solución: Imputación + validación cruzada spatial
- Técnico: Sesgo por zona con mejor reporte (sesgo de vigilancia)
  - Solución: Normalizar por cobertura de reporte
- Climático: Cambios en patrones climáticos (concept drift)
  - Solución: Reentrenamiento semanal, monitoring con Evidently

**Despliegue (4/5):** Implementable pero requiere integración
- Hardware: Servidor + scheduler (Airflow)
- Interfaz: Dashboard Streamlit con mapas de calor
- Integración: Sistema nacional vigilancia epidemiológica (HCIS)
- Escalabilidad: Replicable a otros departamentos
- Personal: Capacitación médicos 1-2 semanas

**Restricción Principal:** ACCESO A DATOS SEDES (menor fricción que antes, pero requiere email)
