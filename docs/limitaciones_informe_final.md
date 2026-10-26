# Limitaciones conocidas del sistema (TASK-036)

Texto base para la sección de limitaciones del informe final. El informe vive fuera
del repositorio: **este texto debe pegarse allí** y la tarea solo se da por cerrada
cuando la sección esté en el informe entregado.

Cada limitación indica qué mitiga el sistema hoy, qué no mitiga y dónde está el detalle
(`docs/risk_register.md`, M-xx). Las cifras salen de los documentos fuente; aquí no se
redondean a favor del modelo.

## 1. Las tres limitaciones que pide la tarea

### 1.1 Sesgo de vigilancia
Los casos que el sistema ve son los que se **notifican**. Una zona con mejor
infraestructura de salud o mejor reporte aparece con más casos aunque no tenga más
enfermedad, y una zona con poco reporte puede parecer tranquila. El modelo aprende de
lo notificado, no de lo ocurrido, y puede reforzar esa desigualdad.

- *Qué mitiga hoy:* nada del sesgo en sí. La interfaz presenta el riesgo como apoyo a
  la decisión humana, no como veredicto, y cada alerta muestra las variables que la
  explican para que un técnico pueda cuestionarla.
- *Qué no mitiga:* no hay corrección por capacidad de reporte ni por población.
- *Para reducirlo:* incorporar población y número de establecimientos por municipio.

### 1.2 Retraso de reporte
Los datos más recientes están incompletos: la última semana epidemiológica muestra
alrededor de 39 % de los casos que terminan reportándose (M-07). Tomarla como
definitiva subestima el riesgo reciente.

- *Qué mitiga hoy:* los datos se marcan como provisionales en el contrato de datos, y
  el horizonte de la predicción (3 a 4 semanas) deja margen para que el reporte se complete.
- *Qué no mitiga:* el modelo no corrige el retraso; trata las semanas recientes como
  llegan.
- *Para reducirlo:* modelar la curva de completitud del reporte con más semanas de historia.

### 1.3 Cobertura climática irregular
El clima observado (SENAMHI) solo existe para **4 estaciones**: Guayaramerín, Ixiamas,
Palos Blancos y San Buenaventura. La epidemiología cubre más municipios (28 con dengue,
21 con malaria), pero sin clima real. Además, SENAMHI (observado) y NASA POWER
(modelado) no son equivalentes (M-12).

- *Qué mitiga hoy:* los valores imputados se marcan (`es_dato_imputado`), nunca se
  imputa en silencio, y la **confianza de la predicción** baja cuando faltan datos
  climáticos (NFR-007). La lista de municipios sin cobertura está en
  `docs/municipios_sin_cobertura_climatica.md`.
- *Qué no mitiga:* la confianza mide la completitud de los datos, **no** qué tan bien
  acierta el modelo (M-13).
- *Para reducirlo:* pedir las estaciones adicionales de esa lista.

## 2. Limitaciones del componente inteligente

| Limitación | Qué significa | Riesgo |
|---|---|---|
| **El modelo no supera de forma concluyente a una regla simple.** En t+3, F1 0,33 contra 0,48 de «casos recientes». | Es una línea base exploratoria, no un sistema validado. | M-01 |
| **Solo 13 semanas de historia (SE 1-13 de 2026).** | No hay estacionalidad ni validación entre años. | M-02 |
| **La etiqueta no es un brote.** Se predice «al menos un caso en t+3». | No hay definición epidemiológica de brote acordada con salud. | M-04 |
| **Malaria sin modelo.** La fuente solo entrega un acumulado por municipio. | Se muestran casos observados; nunca se inventan predicciones (ADR-005). | M-03 |
| **Los objetivos NFR-001 (precisión espacial) y NFR-002 (anticipación) no se pueden validar.** | No hay fuente de brotes confirmados; `GET /modelo/desempeno` existe pero devuelve «sin brotes confirmados». | M-08 |
| **Las alertas dependen de un umbral referencial (70 %).** Con él, ninguna predicción actual (15 a 44 %) alerta. | El umbral real debe definirlo el equipo de salud. | M-09 |

## 3. Limitaciones de alcance y de datos

- **Zona piloto de 4 municipios** (REQ-017); el resto del país no está implementado (M-06).
- **Geometría referencial:** cada municipio piloto es un cuadrado de unos 5 km, no el límite
  oficial del INE; no sirve para calcular áreas ni distancias (M-05).
- **Sin datos de pacientes:** todo es conteo agregado (REQ-020). Es una protección y también un
  límite: no hay detalle individual (M-14).
- **Reglas de campañas y recomendaciones provisionales:** los cortes (33,33 % y 66,67 %) y los
  textos son decisiones del MVP, no protocolos de SEDES (M-15).

## 4. Limitaciones técnicas y de seguridad

- **Sesión en el navegador:** el refresh token se guarda en `sessionStorage`; quedaría
  expuesto ante un XSS (M-11).
- **Dependencias con avisos** (`python-multipart`, `python-jose`) y **sin límite de intentos
  de login ni cabeceras en nginx** (M-16, M-17; `docs/revision_seguridad.md`).
- **Rendimiento:** `GET /zonas/riesgo` cumple NFR-004 solo con 1 a 5 usuarios simultáneos; con
  350 municipios simulados el p95 fue 423 ms con 1 usuario y 4 229 ms con 10 (medición local
  con datos simulados, no de Render) (M-18).
- **Infraestructura gratuita:** la API de Render se duerme tras 15 minutos sin tráfico y
  tarda cerca de un minuto en despertar; Neon gratuito suspende el cómputo sin uso y no
  garantiza copias de seguridad (`docs/guia_despliegue_render_neon.md` §8).

## 5. Cómo debe leerse el sistema

Es un **prototipo funcional de apoyo a la decisión**: integra datos, predice dengue a 3-4
semanas con un modelo explicable, genera alertas con justificación y las presenta por rol.
**No** es un sistema validado ni sustituye el juicio epidemiológico. Pasar de prototipo a
herramienta de uso real requiere, como mínimo: más años de datos, una fuente de brotes
confirmados, una definición de brote y de umbral acordada con SEDES, y la revisión de
seguridad firmada por el equipo.
