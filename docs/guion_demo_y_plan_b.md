# Guion de la demostración y Plan B (TASK-045)

Guía para la 2.ª Defensa (Demostración del MVP y Sprint Review 2). La regla de oro de la guía es **no sustituir la demostración por capturas estáticas**, y el Plan B **no maquilla**: si algo falla, se dice y se muestra el registro del fallo.

> Estado al 2026-10-26: la demostración corre **en local**. El despliegue en la nube (gate obligatorio de la guía) sigue pendiente (TASK-004). Hasta que exista, hay que decir con claridad que se defiende un MVP local reproducible y qué falta para desplegarlo.

## 1. Antes del día (1 a 2 días antes)

| # | Paso | Cómo se comprueba |
|---|---|---|
| 1 | **Congelar la versión:** acordar commit y crear el tag `v0.2-mvp`; no mezclar nada más después | `git tag` muestra el tag; todos defienden el mismo commit |
| 2 | **Probar en la máquina de la demo**, no solo en la propia | Se ejecuta la sección 2 completa desde cero |
| 3 | **Correr las pruebas** y registrar el resultado real | `pytest -q` y `npm test`; anotar cuántas pasan y cuáles fallan |
| 4 | **Datos autorizados:** usar solo los CSV del repositorio (sin datos de pacientes) | Revisar `data/processed` |
| 5 | **Preparar el Plan B** (sección 5) | Existe el respaldo y la grabación |
| 6 | **Ensayar** con cronómetro, todo el equipo | Cada persona puede explicar el sistema integrado, no solo su parte |

## 2. Poner el sistema en marcha desde cero

Requisitos: Python 3.12, Node 22 o superior, PostgreSQL con PostGIS. Sin pasos ocultos: todo lo necesario está en esta lista.

```bash
# 1. Base de datos (PostGIS instalado en el sistema; con Docker ver la nota al final)
createdb dengue_malaria && psql dengue_malaria -c "CREATE EXTENSION postgis;"

# 2. Variables (los valores son de ejemplo; nunca se suben al repositorio)
export DATABASE_URL=postgresql://$USER@localhost:5432/dengue_malaria
export SECRET_KEY=una-clave-local-larga-de-al-menos-32-caracteres
export SEED_DEMO_PASSWORD=elegir-una-clave-de-demo

# 3. Esquema y datos de demostración (un comando cada uno)
cd dengue-malaria-prediccion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # en Mac, ver nota sobre xgboost-cpu
alembic upgrade head
python -m app.etl.seed_demo

# 4. Verificar antes de mostrar nada
uvicorn app.main:app --port 8000 &
SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py

# 5. Interfaz
cd frontend && npm ci && npm run dev      # http://localhost:5173
```

`seed_demo` carga los casos reales del Boletín N.º 13, registra el modelo, genera las predicciones con el pipeline real y crea cinco usuarios `@demo.local` (uno por rol). **No** carga malaria predicha, brotes ni alertas, porque no existen esas fuentes (ver riesgos M-03, M-08 y M-09).

> **Mac:** `requirements-ml.txt` pide `xgboost-cpu`, que no tiene versión para macOS. Instalar `xgboost==2.1.1` y el resto a mano.

### Alternativa con Docker (verificada el 2026-10-26 en un Mac con Apple Silicon)

Sin Docker Desktop: `brew install colima docker docker-compose`, registrar el plugin (`"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` en `~/.docker/config.json`) y `colima start --cpu 4 --memory 6 --disk 40`. Luego, desde `dengue-malaria-prediccion/` y con un `.env` copiado de `.env.example` (con claves propias; está ignorado por git):

```bash
set -a && . ./.env && set +a
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm -v "$PWD/../data:/data:ro" -e SEED_DEMO_PASSWORD ml python -m app.etl.seed_demo
docker compose up -d api web          # interfaz en http://localhost:8080, API en :8000
SMOKE_URL=http://localhost:8080/api SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py
```

Detalles que importan: (1) los datos no viajan en la imagen `ml`, por eso el `-v …/data:/data:ro`; (2) la contraseña de demo hay que pasarla con `-e SEED_DEMO_PASSWORD`; (3) la imagen `postgis/postgis:16-3.4` solo existe para amd64, así que en un Mac con Apple Silicon corre emulada (funciona, un poco más lenta, y Docker avisa de la diferencia de plataforma); (4) la imagen `api` es ligera a propósito (sin pandas ni xgboost): `tests/test_api_ligera.py` vigila que la API no los importe.

## 3. Guion (≈ 10 minutos)

Sigue el orden de la guía: problema → arquitectura → pipeline e IA → resultados → **demo en vivo** → pruebas → repositorio → riesgos.

| Min | Parte | Qué decir y mostrar | Evidencia |
|---|---|---|---|
| 0:00 | Problema | Anticipar brotes de dengue y malaria con 3 a 4 semanas de ventaja; zona piloto de 4 municipios | `docs/product_goal.md` |
| 1:00 | Arquitectura | El diagrama real, no el aspiracional: persona → interfaz → API → base ← modelo | `docs/arquitectura_actual.md` |
| 2:00 | Pipeline e IA | CSV reproducibles (DVC) → ingesta → modelo XGBoost + SHAP | `dvc.yaml`, `app/ml/` |
| 3:00 | Resultados | **El modelo no supera a la regla simple en t+3**; lo decimos y mostramos el porqué | `docs/resultados_experimentales.md` |
| 4:00 | **Demo en vivo** | Ver sección 4 | El propio sistema |
| 7:30 | Pruebas | `pytest -q` y `npm test` en vivo; cobertura de ingesta, limpieza y predicción sobre 70 % | `pytest --cov=app/etl --cov=app/ml` |
| 8:30 | Repositorio | Commits, ramas, PR, ADR, README | GitHub |
| 9:30 | Riesgos | Los de la sección "Actualización al MVP" del registro, dichos en voz alta | `docs/risk_register.md` |

## 4. La demostración en vivo, paso a paso

Caso principal: **una autoridad de salud entra, ve el riesgo y un epidemiólogo ve por qué.**

1. **Acceso.** Entrar como `autoridad@demo.local`. Mostrar un intento con contraseña incorrecta: mensaje claro, sin pistas sobre si el correo existe.
2. **Malaria (vista de entrada).** Aparecen **450 casos acumulados** en 3 municipios (Guayaramerín 293, Ixiamas 156, San Buenaventura 1). Señalar el aviso: *no hay predicción de malaria* y por qué (ADR-005).
3. **Dengue.** Cambiar a Dengue: probabilidades por municipio (en la corrida del 2026-10-26: Guayaramerín 44 %, Ixiamas 43 %, Palos Blancos 23 %, San Buenaventura 15 %; pueden variar si se reentrena). Elegir una zona: la autoridad ve el resumen y la invitación a pedir el detalle técnico.
4. **Otro rol.** Salir y entrar como `epidemiologo@demo.local`: ahora aparecen "Qué influyó en esta predicción" y la pestaña **Historial**. Es el mismo dato con respuesta distinta **desde el servidor** (no se oculta en pantalla).
5. **Prueba extremo a extremo.** En la terminal: `pytest tests/e2e -q`. Recorre el mismo camino automáticamente.
6. **Manejo de errores y diagnóstico** (la guía lo exige en vivo):
   - Entrada inválida: `curl -s -X POST localhost:8000/auth/login -d "username=x"` → 422 sin devolver lo enviado.
   - Dependencia caída, sin tocar la base real: levantar otra API apuntando a un puerto vacío y consultar su estado.
     ```bash
     DATABASE_URL=postgresql://x:y@127.0.0.1:1/z uvicorn app.main:app --port 8001 &
     curl -i localhost:8001/health        # 200: la API sigue viva
     curl -i localhost:8001/health/ready  # 503: la base no responde
     ```
   - Mostrar el log: cada línea trae el `request_id` que también devuelve la respuesta (`X-Request-ID`); no aparecen contraseñas ni correos.

## 5. Plan B (preparar con tiempo, sin maquillar)

| Si falla… | Plan |
|---|---|
| La interfaz o la API | Reiniciar con la sección 2 (2 min). Si no arranca, mostrar el **log del error** y pasar al respaldo |
| La base de datos | Restaurar el respaldo: `pg_restore -d dengue_malaria respaldo_demo.dump` |
| El despliegue o la red | Se defiende en local; el despliegue es un riesgo declarado (M-10) |
| Todo lo anterior | Mostrar la **grabación de una ejecución real**, diciendo explícitamente que es una grabación |

Qué preparar:
- **Respaldo de base:** con el sistema funcionando, `pg_dump -Fc dengue_malaria > respaldo_demo.dump` (guardarlo fuera del repositorio).
- **Grabación real:** grabar la pantalla de una ejecución completa de la sección 4 el día del ensayo. No se edita ni se reemplaza por capturas.
- **Registro de pruebas:** guardar la salida real de `pytest` y `npm test`, incluidas las fallas si las hubiera.

Un Plan B que oculta un error es un antipatrón fatal. Si una prueba falla el día de la defensa, **se dice**, se muestra el resultado real y se explica el porqué.

## 6. Preguntas probables (respuestas honestas)

- **¿El modelo funciona?** Funciona de punta a punta, pero en t+3 no supera a una regla simple (F1 0,33 contra 0,48) y con 13 semanas no puede generalizar. Es una línea base exploratoria.
- **¿Por qué no hay predicción de malaria?** La fuente entrega un solo total por municipio, sin semanas; repartirlo habría inventado datos (ADR-005).
- **¿Qué significa "confianza alta"?** Que faltan pocos datos climáticos; **no** que el modelo acierte (NFR-007).
- **¿Qué es un brote aquí?** Todavía no hay una definición epidemiológica; la etiqueta es "al menos un caso en 3 semanas".
- **¿Por qué los cuadrados en el mapa?** Son referenciales (≈ 5 km); no tenemos los polígonos oficiales del INE.
- **¿Hay datos de pacientes?** No: solo conteos agregados por municipio y semana.
- **¿Qué falta?** Despliegue en la nube, alertas automáticas (TASK-015), tarea semanal (TASK-016), fuente de brotes confirmados y las vistas de priorización de campañas.

## 7. Checklist del día

- [ ] Versión congelada (tag) y todos con el mismo commit
- [ ] `smoke_test.py` en verde en la máquina de la demo
- [ ] Respaldo de base y grabación real listos
- [ ] Resultado real de `pytest` y `npm test` a mano
- [ ] Cada integrante puede explicar el flujo completo
