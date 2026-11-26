# Guion de la demostración y Plan B (TASK-045)

Guía para la 2.ª Defensa (Demostración del MVP y Sprint Review 2). La regla de oro de la guía es **no sustituir la demostración por capturas estáticas**, y el Plan B **no maquilla**: si algo falla, se dice y se muestra el registro del fallo.

> Estado al 2026-10-26: la demostración corre **en local** con todos los municipios del Boletín N.º 13. La API está desplegada en Render (TASK-004; `/health/ready` responde), pero la base de Neon todavía no tiene los datos de demostración y la interfaz no está desplegada: hay que decirlo con claridad.

## 1. Antes del día (1 a 2 días antes)

| # | Paso | Cómo se comprueba |
|---|---|---|
| 1 | **Congelar la versión:** acordar commit y crear el tag `v0.2-mvp`; no mezclar nada más después | `git tag` muestra el tag; todos defienden el mismo commit |
| 2 | **Probar en la máquina de la demo**, no solo en la propia | Se ejecuta la sección 2 completa desde cero |
| 3 | **Correr las pruebas** y registrar el resultado real | `pytest -q` y `npm test`; anotar cuántas pasan y cuáles fallan |
| 4 | **Datos autorizados:** usar solo los CSV del repositorio (sin datos de pacientes) | Revisar `data/processed` |
| 5 | **Preparar el Plan B** (sección 5) | Existe el respaldo de la base y el registro real de pruebas |
| 6 | **Ensayar** con cronómetro, todo el equipo | Cada persona puede explicar el sistema integrado, no solo su parte |

## 2. Poner el sistema en marcha desde cero

> **La receta completa y probada paso a paso está en [`guia_ejecucion_desde_cero.md`](./guia_ejecucion_desde_cero.md)**, incluidas todas las pruebas. Lo de abajo es el resumen original.

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
python -m app.etl.seed_demo --todos-los-municipios --fecha 2026-03-30

# 4. Verificar antes de mostrar nada
uvicorn app.main:app --port 8000 &
SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py

# 5. Interfaz
cd frontend && npm ci && npm run dev      # http://localhost:5173
```

`seed_demo` carga los casos reales del Boletín N.º 13, registra el modelo, genera las predicciones con el pipeline real y crea cinco usuarios `@demo.local` (uno por rol). **No** carga malaria predicha ni brotes confirmados, porque no existen esas fuentes (riesgos M-03 y M-08).

- `--todos-los-municipios` amplía antes el catálogo (ADR-007): 42 municipios, con **28 con dengue (341 casos) y 21 con malaria (1.615 casos)**. Sin esa opción solo entra la zona piloto de 4.
- `--fecha 2026-03-30` genera las predicciones al cierre de los datos (SE 13), así que la fecha estimada de riesgo es el 20 de abril de 2026 y no una fecha de noviembre que los datos no respaldan.
- Las alertas las crea `evaluacion_alertas` con el umbral vigente (70 % por defecto). Con todos los municipios se emiten **3** (Santa Cruz de la Sierra 84 %, La Asunta 80 %, Caranavi 71 %). Como su fecha objetivo (abril) ya pasó, el Resumen las cuenta como **emitidas, no vigentes**. Es lo correcto y se explica en la demo.

> **Mac:** `requirements-ml.txt` pide `xgboost-cpu`, que no tiene versión para macOS. Instalar `xgboost==2.1.1` y el resto a mano.

### Alternativa con Docker (verificada el 2026-10-26 en un Mac con Apple Silicon)

Sin Docker Desktop: `brew install colima docker docker-compose`, registrar el plugin (`"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` en `~/.docker/config.json`) y `colima start --cpu 4 --memory 6 --disk 40`. Luego, desde `dengue-malaria-prediccion/` y con un `.env` copiado de `.env.example` (con claves propias; está ignorado por git):

```bash
set -a && . ./.env && set +a
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm -v "$PWD/../data:/data:ro" -e SEED_DEMO_PASSWORD ml python -m app.etl.seed_demo --todos-los-municipios --fecha 2026-03-30
docker compose up -d api web          # interfaz en http://localhost:8080, API en :8000
SMOKE_URL=http://localhost:8080/api SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD="$SEED_DEMO_PASSWORD" python scripts/smoke_test.py
```

Detalles que importan: (1) los datos no viajan en la imagen `ml`, por eso el `-v …/data:/data:ro`; (2) la contraseña de demo hay que pasarla con `-e SEED_DEMO_PASSWORD`; (3) la imagen `postgis/postgis:16-3.4` solo existe para amd64, así que en un Mac con Apple Silicon corre emulada (funciona, un poco más lenta, y Docker avisa de la diferencia de plataforma); (4) la imagen `api` es ligera a propósito (sin pandas ni xgboost): `tests/test_api_ligera.py` vigila que la API no los importe.

## 3. Guion (≈ 10 minutos)

Sigue el orden de la guía: problema → arquitectura → pipeline e IA → resultados → **demo en vivo** → pruebas → repositorio → riesgos.

| Min | Parte | Qué decir y mostrar | Evidencia |
|---|---|---|---|
| 0:00 | Problema | Anticipar brotes de dengue y malaria con 3 a 4 semanas de ventaja; los 28 municipios con dengue y 21 con malaria del Boletín N.º 13 | `docs/product_goal.md` |
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
2. **Resumen (vista de entrada).** 341 casos de dengue en 28 municipios, 1.615 de malaria en 21, 3 zonas en riesgo alto y la serie semanal (la SE 13 marcada como provisional). Señalar "0 alertas vigentes, 3 emitidas": la fecha objetivo (abril) ya pasó.
3. **Mapa.** En Malaria, los casos acumulados por municipio (Riberalta 682, Guayaramerín 293, Ixiamas 156…) y el aviso de que *no hay predicción de malaria* y por qué (ADR-005). En Dengue, las probabilidades (corrida del 2026-10-26: Santa Cruz de la Sierra 84 %, La Asunta 80 %, Caranavi 71 %; pueden variar si se reentrena). Elegir una zona: la autoridad ve el resumen y la invitación a pedir el detalle técnico.
4. **Otro rol.** Salir y entrar como `epidemiologo@demo.local`: ahora aparecen "Qué influyó en esta predicción" y la pestaña **Historial**. Es el mismo dato con respuesta distinta **desde el servidor** (no se oculta en pantalla).
5. **Alertas (REQ-009, REQ-005).** En la pestaña **Alertas** ("Todas las emitidas") aparecen las 3 alertas del umbral de 70 %, cada una con su justificación y sus variables SHAP.
6. **Umbral configurable (REQ-010), opcional.** Como admin: `curl -X POST localhost:8000/admin/umbrales -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"enfermedad_id": <id de dengue>, "umbral_probabilidad_pct": 55}'` y luego `python -m app.ml.evaluacion_alertas`: se suman las zonas entre 55 y 70 % (San Borja, Montero, Buena Vista). Las alertas son inmutables: para repetir la demo desde cero hay que rehacer la base (sección 2).
7. **Cargar un boletín (REQ-014).** Como epidemiólogo, pestaña **Datos**. Subir `data/boletines/SE21.pdf`: se rechaza con el motivo (ese boletín ya no trae la tabla municipal). Subir `SE13.pdf`: la tabla se verifica contra los totales impresos y no hay nada nuevo que guardar, porque ya está cargado. Explicar que el sitio del Ministerio bloquea la descarga automática y que el Resumen avisa cuando faltan boletines.
8. **Prueba extremo a extremo.** En la terminal: `pytest tests/e2e -q`. Recorre el mismo camino automáticamente.
9. **Manejo de errores y diagnóstico** (la guía lo exige en vivo):
   - Entrada inválida: `curl -s -X POST localhost:8000/auth/login -d "username=x"` → 422 sin devolver lo enviado.
   - Dependencia caída, sin tocar la base real: levantar otra API apuntando a un puerto vacío y consultar su estado.
     ```bash
     DATABASE_URL=postgresql://x:y@127.0.0.1:1/z uvicorn app.main:app --port 8001 &
     curl -i localhost:8001/health        # 200: la API sigue viva
     curl -i localhost:8001/health/ready  # 503: la base no responde
     ```
   - Mostrar el log: cada línea trae el `request_id` que también devuelve la respuesta (`X-Request-ID`); no aparecen contraseñas ni correos.

## 5. Plan B

**El Plan B es tener dos laptops con el sistema listo.** Si una falla, se sigue con la otra. La presentación y el ensayo los prepara el grupo; no son una tarea del repositorio.

| Si falla… | Plan |
|---|---|
| La interfaz o la API en una laptop | Pasar a la segunda laptop (misma versión, `v0.2-mvp`) |
| Una laptop no arranca el sistema | Reiniciar con la sección 2 (2 min) o usar la otra |
| La red o el despliegue | Se defiende en local en cualquiera de las dos; el despliegue en Render es un riesgo declarado (M-10) |

Antes de la defensa, en **las dos** laptops: la versión `v0.2-mvp`, el sistema arrancado con la sección 2 y `scripts/smoke_test.py` en verde.

Un Plan B que oculta un error es un antipatrón fatal. Si algo falla el día de la defensa, **se dice**, se muestra el resultado real y se explica el porqué. Nunca se sustituye la demostración por capturas.

## 6. Preguntas probables (respuestas honestas)

- **¿El modelo funciona?** Funciona de punta a punta, pero en t+3 no supera a una regla simple (F1 0,33 contra 0,48) y con 13 semanas no puede generalizar. Es una línea base exploratoria.
- **¿Por qué no hay predicción de malaria?** La fuente entrega un solo total por municipio, sin semanas; repartirlo habría inventado datos (ADR-005).
- **¿Qué significa "confianza alta"?** Que faltan pocos datos climáticos; **no** que el modelo acierte (NFR-007).
- **¿Qué es un brote aquí?** Todavía no hay una definición epidemiológica; la etiqueta es "al menos un caso en 3 semanas".
- **¿Por qué hay cuadrados en el mapa?** Los 4 municipios piloto y Santa Rosa (Beni) usan un cuadrado referencial (≈ 5 km). Los otros 37 tienen el límite administrativo de OpenStreetMap, simplificado a unos 110 m para que el mapa cargue rápido. No son los polígonos oficiales del INE.
- **¿Por qué 0 alertas vigentes si hay 3?** Las predicciones se generan al cierre de los datos (SE 13), así que apuntan a abril de 2026, que ya pasó. Faltan boletines nuevos con la tabla municipal; el Resumen lo avisa.
- **¿Por qué Santa Cruz tiene 84 % con 9 casos y San Borja 64 % con 140?** Porque el modelo es una línea base con 13 semanas que no supera a la regla simple (M-01). El ranking por municipio todavía no es creíble y lo declaramos (M-20); el sistema está listo para reentrenar cuando haya más datos.
- **¿Todas las predicciones son igual de confiables?** No. Alto Beni usa clima tomado de coordenadas equivocadas (ciudad de La Paz) por un error de la primera geocodificación; está declarado en el registro de riesgos.
- **¿Hay datos de pacientes?** No: solo conteos agregados por municipio y semana.
- **¿Qué falta?** Una fuente de brotes confirmados (sin ella no se pueden validar NFR-001 y NFR-002), más datos y años para el modelo, polígonos oficiales y la validación de las reglas de campañas con SEDES. El despliegue (Render + Neon), la tarea semanal y las vistas de campañas ya están hechos.

## 7. Checklist del día

- [ ] Versión congelada (tag) y todos con el mismo commit
- [ ] `smoke_test.py` en verde en la máquina de la demo
- [ ] Segunda laptop lista con el mismo sistema (Plan B)
- [ ] Resultado real de `pytest` y `npm test` a mano
- [ ] Cada integrante puede explicar el flujo completo
