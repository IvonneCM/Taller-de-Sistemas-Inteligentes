# Instrucciones para GitHub Copilot

> Este proyecto sigue Spec Driven Development. Antes de sugerir código,
> considera el contexto de `requirements.md`, `design.md` y `tasks.md` en la
> raíz del repositorio.

## Bloque de instrucciones universal (idéntico al de CLAUDE.md)

### Proyecto

Sistema inteligente de predicción temprana de brotes de dengue/malaria en
Bolivia, orientado a autoridades de salud pública, equipos del SEDES,
médicos epidemiólogos y coordinadores sanitarios municipales. Objetivo:
anticipar brotes con 3-4 semanas de anticipación usando datos
epidemiológicos, climáticos y geoespaciales.

### Stack

- Backend: Python 3.12 + FastAPI
- Base de datos: PostgreSQL 16 + PostGIS
- ML: scikit-learn / XGBoost + SHAP (explicabilidad)
- Frontend: React + Leaflet/Mapbox
- Despliegue: Railway

### Reglas no negociables

1. **No inventar datos reales no verificados.** Marca explícitamente como
   "estimada" o "referencial" cualquier cifra que no venga de una fuente
   verificada del proyecto.
2. **No incluir datos personales de pacientes** en ningún modelo, endpoint,
   log o archivo de prueba.
3. **No generar alertas sin justificación** (`alertas.justificacion` nunca
   nulo; sin variables explicativas, no se crea la alerta).
4. **La tabla `predicciones` es de solo inserción** (nunca UPDATE), para
   permitir auditoría.
5. **`requirements.md` es la fuente de autoridad.** No fabricar requisitos
   no documentados; si falta contexto, sugerir dejar un comentario `# TODO:
   confirmar con el equipo` en vez de asumir.
6. **No exponer credenciales** en código sugerido; usar siempre variables de
   entorno (`app/core/config.py`).
7. Al completar funciones que implementan una tarea de `tasks.md`, incluir
   en el docstring la referencia `REQ-xxx` / `NFR-xxx` correspondiente.

### Manejo de datos incompletos

Los datos epidemiológicos y climáticos de este dominio suelen tener retrasos
de reporte, sesgo de vigilancia entre zonas, y cobertura irregular. No
sugieras código que asuma datos completos o sin ruido por defecto; usa las
utilidades de `app/etl/limpieza.py` cuando corresponda.

## Notas específicas para Copilot

- Prioriza autocompletar siguiendo los tipos definidos en `app/schemas/`
  (Pydantic) y `app/models/` (SQLAlchemy) antes de generar nuevos tipos.
- Al sugerir queries SQL/ORM sobre `municipios`, recuerda que la columna
  `geometria` es de tipo PostGIS — usa funciones espaciales (`ST_Contains`,
  `ST_Intersects`, etc.) en vez de comparaciones numéricas simples.
- No sugieras dependencias nuevas fuera de las listadas en el stack sin que
  el desarrollador lo pida explícitamente.
