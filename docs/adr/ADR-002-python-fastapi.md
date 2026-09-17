# ADR-002: Python 3.12 + FastAPI para el backend

- **Estado:** Aceptado
- **Fecha:** 2026-09-16
- **Decisores:** Equipo SIPTB
- **Relacionado:** `design.md` §1, REQ-001, REQ-006, NFR-010

## Contexto

Se necesita un backend/API REST que exponga predicciones, alertas, mapas de
calor y métricas de desempeño, con autenticación y control por roles (RBAC), y
que conviva con el pipeline de Machine Learning. El proyecto es universitario,
por lo que se prioriza un stack con buen soporte de tipado, documentación
automática y baja fricción para el equipo.

## Alternativas consideradas

1. **FastAPI** (Python 3.12) — tipado, async, OpenAPI automático.
2. **Flask** — minimalista, pero sin validación/esquema ni OpenAPI integrados.
3. **Django + DRF** — baterías incluidas (ORM, admin), pero más pesado y
   opinionado para una API centrada en ML.
4. **Node.js / Express** — buen rendimiento, pero obliga a replicar el
   ecosistema de ML (scikit-learn/XGBoost) en otro lenguaje/servicio.

## Decisión

Usar **Python 3.12 + FastAPI** como framework de backend/API.

## Justificación

- Mantiene un **único lenguaje** entre API y modelado ML (scikit-learn /
  XGBoost / SHAP), evitando un servicio puente.
- Genera **OpenAPI automático**, lo que facilita integrar el frontend React y
  documentar endpoints (design.md §4).
- Soporta modelos con `pydantic` para validar entrada/salida de la ingesta de
  datos (REQ-013).
- Incluye **OAuth2 password flow** listo para el RBAC requerido por REQ-006.

## Consecuencias

- **Positivas:** desarrollo rápido, documentación viva, tipado y validación
  integrados, coherencia con el stack de ML.
- **Negativas / costos:** requiere disciplina para operaciones pesadas en
  background (se apoya en APScheduler/Celery, ver design.md §1); el rendimiento
  puro es menor que Node/Go, aceptable para la carga esperada.
