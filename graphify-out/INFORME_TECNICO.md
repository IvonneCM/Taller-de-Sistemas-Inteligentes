# Informe técnico — Análisis con Graphify (12-oct-2026)

Commit analizado: `9b1b25f` (rama `tani`, árbol limpio al inicio).
Herramienta: `graphifyy` instalado en un venv aparte (`~/.venvs/graphify`), ejecutado con `graphify update .` (extracción de código local con tree-sitter, sin LLM, sin red).

## Artefactos generados (verificados)
- `graphify-out/graph.json` (524 KB), `graph.html` (605 KB), `GRAPH_REPORT.md` (20 KB), `manifest.json`, `cache/`.
- Resultado: 706 nodos, 944 aristas, 84 comunidades. 100 % aristas EXTRACTED, 1 INFERRED.

## Arquitectura identificada
**Hechos comprobados (código y `dvc.yaml`)**
- Pipeline de datos en `scripts/`, orquestado por DVC en este orden: `procesar_clima.py` → `limpieza_datos.py` → `integrar_datos.py` → `eda_integrado.py`.
- Scripts adicionales: `descargar_senamhi.py`, `eda_inicial.py`, `eda_climatico.py`, `linea_base_modelo.py`.
- Backend `dengue-malaria-prediccion/app/`: FastAPI con un único endpoint `/health` en `app/main.py`. Los paquetes `api`, `core`, `etl`, `ml`, `models`, `schemas` y `tests` contienen solo `__init__.py` (esqueleto sin implementar).
- Dependencias externas más conectadas: `pandas`, `matplotlib.pyplot`, `numpy`.
- Sin ciclos de importación detectados.
- Documentación (ADR, C4, riesgos, sprint 1) forma la mayoría de las comunidades del grafo.

**Inferencias (no comprobadas por el grafo)**
- Los "god nodes" son varias funciones `main()` de scripts distintos (22, 20, 14 y 12 aristas). El grafo no las distingue por nombre; es un artefacto de nodos homónimos, no un núcleo único.
- El backend y el pipeline de datos parecen aún no conectados: el grafo no muestra aristas entre `app/` y `scripts/`.

## Limitaciones
- 52 archivos sin clasificar y omitidos: 40 CSV, 8 sin extensión, 2 `.dvc`. **Aunque se pidió incluir todo, los CSV no son un tipo soportado, así que no se procesaron.** Esto también protege los datos.
- 25 archivos `SKILL.md`/comandos fueron tratados como código sin símbolos.
- Extracción PDF omitida (falta `pypdf`); no se instaló.
- Los `.md` entraron como estructura de encabezados, sin extracción semántica con LLM (requeriría `/graphify` en el asistente o API key).
- No capta llamadas dinámicas ni dependencias en tiempo de ejecución.

## Validación (sección 7)
- Sin errores en la ejecución: sí.
- Artefactos existen: sí.
- Grafo con componentes reales: sí (scripts, `main.py` y docs coinciden con el repo).
- Exclusiones sensibles: `.env` y `.venv` ignorados por `.gitignore`; solo `.env.example` está presente. Búsqueda de "secret/password" en el grafo: solo coincide un encabezado de `docs/controles_seguridad.md`, no credenciales.
- Código funcional no alterado: sí (`git status` solo muestra `graphify-out/` sin seguimiento).

## Pendiente de decisión
- `graphify-out/` no está en `.gitignore`. Antes de versionarlo, confirmar la política del proyecto (sección 9). El grafo incluye rutas y nombres internos del repositorio.
