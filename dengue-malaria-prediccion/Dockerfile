# Python fijado en 3.12 (stack de CLAUDE.md / design.md §1).
# Dos imagenes desde este archivo (docker build --target <api|ml>):
#   api -> solo sirve la API (ligera). Es la ULTIMA etapa a proposito: un
#          `docker build .` sin --target (p. ej. Railway) construye la API.
#   ml  -> ETL, limpieza, prediccion semanal y SHAP (pandas, xgboost, shap).
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Dependencias primero: la capa se reutiliza si los requirements no cambian.
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

RUN useradd --create-home appuser


FROM base AS ml
COPY requirements-ml.txt .
RUN pip install -r requirements-ml.txt
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
USER appuser
# Sin servidor: el comando lo define quien lo ejecuta, p. ej.
#   docker compose run --rm ml python -m app.etl.seed_catalogo
CMD ["python"]


FROM base AS api
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
USER appuser

# Railway inyecta PORT; en local queda 8000. Sin secretos en la imagen:
# DATABASE_URL, SECRET_KEY, etc. se pasan como variables de entorno.
EXPOSE 8000
# --proxy-headers: detras del proxy HTTPS de Railway, las URLs generadas por la
# API conservan https.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
