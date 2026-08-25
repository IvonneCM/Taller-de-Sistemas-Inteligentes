# Sistema de Predicción Temprana de Brotes de Dengue/Malaria (Bolivia)

Proyecto universitario: predicción de zonas con riesgo de brote de dengue o
malaria con 3-4 semanas de anticipación, usando datos epidemiológicos,
climáticos y geoespaciales, para apoyar a SEDES, autoridades de salud y
coordinadores municipales.

## Documentación (leer en este orden)

1. [`requirements.md`](./requirements.md) — qué debe hacer el sistema
2. [`design.md`](./design.md) — cómo está construido (arquitectura, modelo de datos, API)
3. [`tasks.md`](./tasks.md) — plan de implementación paso a paso
4. [`CONTEXT.md`](./CONTEXT.md) — en qué tarea vamos ahora mismo
5. [`CLAUDE.md`](./CLAUDE.md) — reglas para agentes de IA que trabajen en este repo

## Stack

- **Backend:** Python 3.12 + FastAPI
- **Base de datos:** PostgreSQL 16 + PostGIS
- **ML:** scikit-learn / XGBoost + SHAP (explicabilidad)
- **Frontend:** React + Leaflet/Mapbox (no incluido en este paquete inicial)
- **Despliegue:** Railway

## Requisitos previos

- Python 3.12+
- PostgreSQL 16+ con extensión PostGIS disponible
- VS Code con las extensiones recomendadas (se sugieren automáticamente al
  abrir la carpeta — ver `.vscode/extensions.json`)

## Puesta en marcha local

```bash
# 1. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales (DATABASE_URL, SECRET_KEY, etc.)

# 4. Crear la base de datos y habilitar PostGIS
createdb dengue_malaria
psql -d dengue_malaria -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# 5. Ejecutar migraciones (una vez que existan, ver TASK-005 en tasks.md)
alembic upgrade head

# 6. Levantar el servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

Verificar que todo funciona:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Uso desde VS Code

Este repositorio incluye configuración lista para VS Code:

- **`.vscode/settings.json`** — intérprete de Python, formateo automático, conexión sugerida a PostgreSQL vía SQLTools.
- **`.vscode/launch.json`** — configuraciones de depuración para `uvicorn` y `pytest`.
- **`.vscode/tasks.json`** — tareas rápidas (Ctrl+Shift+P → "Tasks: Run Task"): instalar dependencias, levantar servidor, correr migraciones, ejecutar tests con cobertura.
- **`.vscode/extensions.json`** — extensiones recomendadas, incluyendo **Claude Code** y **GitHub Copilot**.

## Trabajar con Claude Code

1. Abrir esta carpeta en VS Code (o la terminal, si usas Claude Code en modo CLI).
2. Iniciar Claude Code (extensión o `claude` en terminal).
3. Usar el prompt inicial de [`FIRST_PROMPT.md`](./FIRST_PROMPT.md) para arrancar la Fase 1 según `tasks.md`.
4. Claude Code debe leer `CONTEXT.md` al inicio de cada sesión y actualizarlo al final (ver `CLAUDE.md`).

## Estructura del proyecto

```
dengue-malaria-prediccion/
├── app/
│   ├── main.py
│   ├── core/            # configuración, seguridad
│   ├── models/          # modelos ORM (SQLAlchemy + PostGIS)
│   ├── schemas/         # esquemas Pydantic
│   ├── api/routes/      # endpoints REST
│   ├── etl/conectores/  # ingesta de datos por fuente
│   └── ml/              # features, entrenamiento, predicción, explicabilidad
├── tests/
├── alembic/              # migraciones (se inicializa en TASK-001/005)
├── requirements.md
├── design.md
├── tasks.md
├── CONTEXT.md
├── CLAUDE.md
├── .github/copilot-instructions.md
└── FIRST_PROMPT.md
```

## Notas importantes

- No se manejan datos personales de pacientes (ver REQ-020) — todo dato
  epidemiológico se trabaja agregado por municipio y fecha.
- Cualquier cifra de precisión o desempeño mostrada en código o
  documentación debe marcarse como "estimada/referencial" hasta ser validada
  con datos reales del piloto.
- Ver preguntas abiertas en `design.md` §10 antes de implementar los
  conectores de ingesta (TASK-008, TASK-009).
