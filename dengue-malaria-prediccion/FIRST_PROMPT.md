# Primer prompt para Claude Code

Copia y pega el siguiente bloque como tu primer mensaje a Claude Code,
dentro de esta carpeta del proyecto (`dengue-malaria-prediccion/`), una vez
que ya tengas Python instalado y (si es posible) PostgreSQL disponible
localmente.

---

```
Estamos empezando la implementación de este proyecto. Antes de escribir
cualquier código, lee en este orden:

1. CONTEXT.md — para saber en qué tarea vamos.
2. requirements.md — qué debe hacer el sistema.
3. design.md — arquitectura, modelo de datos y endpoints.
4. tasks.md — plan de tareas ordenado.
5. CLAUDE.md — reglas no negociables para este proyecto (no inventar
   datos, no exponer datos personales de pacientes, no generar alertas
   sin justificación, tabla de predicciones inmutable, etc.).

Contexto del proyecto: sistema de predicción temprana de brotes de dengue
y malaria en Bolivia (3-4 semanas de anticipación), usando datos
epidemiológicos, climáticos y geoespaciales. Stack: Python + FastAPI +
PostgreSQL/PostGIS, ML con scikit-learn/XGBoost + SHAP para
explicabilidad. Es un proyecto universitario, así que prioriza soluciones
simples y correctas sobre soluciones sofisticadas.

Quiero que empecemos por la Fase 1 de tasks.md (Infraestructura base),
empezando por TASK-001:

- Verifica la estructura de carpetas ya creada en app/ (ya tiene los
  __init__.py y un app/main.py mínimo con endpoint /health).
- Completa requirements.txt si falta algo (ya existe una versión inicial
  en la raíz del proyecto — revísala antes de agregar dependencias
  nuevas).
- Configura app/core/config.py para leer las variables de entorno listadas
  en .env.example (DATABASE_URL, SECRET_KEY, ALGORITHM,
  ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, ENVIRONMENT)
  usando pydantic-settings. No hardcodees ningún secreto.
- No avances a TASK-002 (PostGIS) ni a tareas de la Fase 2 todavía.

Antes de escribir código, dime brevemente tu plan para TASK-001 y espera
mi confirmación. Al terminar, ejecuta la verificación descrita en
tasks.md para TASK-001 y muéstrame el resultado.

Si encuentras algo ambiguo entre requirements.md y design.md, o si crees
que falta información (por ejemplo sobre las preguntas abiertas de
design.md §10), pregúntame antes de asumir.
```

---

## Notas sobre este prompt

- Está diseñado para **una sola tarea a la vez** (TASK-001), siguiendo el
  principio de atomicidad de `tasks.md` — evita pedirle a Claude Code que
  "implemente todo el backend" de una vez.
- Pide **plan antes de código** para poder corregir el rumbo temprano,
  especialmente útil en un proyecto universitario donde el aprendizaje
  del proceso importa tanto como el resultado.
- Después de cerrar TASK-001, el siguiente prompt debería ser simplemente:
  `"Continuemos con TASK-002 de tasks.md"` — Claude Code ya tiene el
  contexto necesario en `CLAUDE.md` para retomarlo correctamente, y
  actualizará `CONTEXT.md` al cierre de la sesión según el protocolo
  definido ahí.
- Si abres una sesión nueva (ventana nueva, otro día), el primer mensaje
  puede ser simplemente: `"Retoma el proyecto, lee CONTEXT.md primero"`.
