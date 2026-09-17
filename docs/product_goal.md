# Product Goal: Predicción de Brotes de Dengue/Malaria (Time Series + Geospatial)

### Enunciado

Para **autoridades de salud pública y equipos de prevención en SEDES**, construiremos un **sistema que predice dónde habrá brotes de dengue/malaria 3-4 semanas adelante**, que permite **activar campañas de fumigación preventiva y asignar recursos médicos antes de que ocurra el brote**, utilizando datos epidemiológicos históricos y datos climáticos públicos.

---

### Verificación de calidad

| Criterio | Cumple | Evidencia |
|----------|--------|-----------|
| ¿Usuario real entiende para qué existe? |  SÍ | "Autoridad sanitaria recibe predicción: 'Zona X tendrá brote en 3 semanas, riesgo 85%', comienza fumigación HOY" |
| ¿Usuario identificado? | SÍ | Médicos epidemiólogos, coordinadores SEDES, autoridades sanitarias municipales |
| ¿Problema específico? | SÍ | Bolivia 100k+ casos dengue/año; brotes llegan sin aviso; recursos sanitarios limitados; muertes prevenibles |
| ¿Métrica de éxito? | SÍ | Predice brote 2-4 semanas antes con ≥75% de precisión espacial (NFR-001); permite activación de protocolos preventivos |
| ¿Sin tecnología como fin? | SÍ | No menciona "LSTM" o "Prophet"; resultado es "anticipar brotes para prevenir" |

### Contexto de éxito

- **Restricción principal:** Datos climáticos/epidemiológicos con gaps (algunas semanas falta info); variabilidad entre regiones
- **Métrica clave:** Precisión espacial (por zona) ≥75% (NFR-001); anticipación mínima de 2 semanas (NFR-002), con objetivo de diseño de 3-4 semanas
- **Criterio de aceptación:** en la zona piloto, el modelo predice el brote al menos 2 semanas antes de la confirmación clínica. La zona piloto de facto (por disponibilidad real de datos) son los 4 municipios con cruce de clima+epidemiología: Guayaramerín (Beni), Ixiamas, Palos Blancos y San Buenaventura (La Paz) — ver `design.md` §10, aún sin confirmación oficial del equipo.
- **Riesgo identificado:** Datos incompletos (falta estaciones meteorológicas en zonas rurales); sesgo por zona con mejor reporte

### Escalabilidad

- Replicable a otros departamentos (Cochabamba, Santa Cruz, Potosí)
- Escalable a predicción de otras enfermedades (malaria, dengue hemorrágico)
- Integración con sistema nacional de vigilancia epidemiológica
- Dashboard para autoridades sanitarias + alertas SMS

---

