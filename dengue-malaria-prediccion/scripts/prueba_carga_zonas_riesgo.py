"""Prueba de carga de GET /zonas/riesgo (TASK-033, NFR-004).

Objetivo: p95 < 2 s con hasta 350 municipios. DATOS SIMULADOS: los municipios,
poligonos y predicciones de esta prueba son sinteticos y solo sirven para medir
latencia; no representan casos reales (CLAUDE.md regla 1).

No toca ninguna base existente: crea una base TEMPORAL (carga_zonas_riesgo) en
el PostgreSQL+PostGIS LOCAL, aplica las migraciones, carga los datos simulados,
levanta la API (un solo worker, como el plan gratuito de Render), mide y borra
la base al terminar. Se niega a correr contra hosts que no sean locales.

Uso (desde dengue-malaria-prediccion/, con el entorno virtual activado):
    docker compose up -d db
    python scripts/prueba_carga_zonas_riesgo.py \\
        --admin-url postgresql://postgres:CLAVE@127.0.0.1:5433/postgres

Limite conocido: mide el equipo donde se ejecuta, no Render ni Neon.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]
BASE_TEMPORAL = "carga_zonas_riesgo"
HOSTS_LOCALES = {"localhost", "127.0.0.1", "::1", "db"}
EMAIL = "carga@prueba.local"
PASSWORD = secrets.token_urlsafe(18)  # efimera: la base se borra al terminar
VERTICES_POR_CUADRANTE = 75  # ~300 vertices por poligono, como un municipio real


def url_con_base(admin_url: str, base: str) -> str:
    partes = urlsplit(admin_url)
    return urlunsplit(partes._replace(path=f"/{base}"))


def verificar_local(admin_url: str) -> None:
    host = urlsplit(admin_url).hostname
    if host not in HOSTS_LOCALES:
        sys.exit(f"Se niega a correr contra {host!r}: solo bases locales.")


def crear_base(admin_url: str) -> None:
    motor = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with motor.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {BASE_TEMPORAL}"))
        c.execute(text(f"CREATE DATABASE {BASE_TEMPORAL}"))
    motor.dispose()


def borrar_base(admin_url: str) -> None:
    motor = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with motor.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {BASE_TEMPORAL} WITH (FORCE)"))
    motor.dispose()


def entorno(url_base: str) -> dict:
    env = dict(os.environ)
    env.update(
        DATABASE_URL=url_base,
        SECRET_KEY=secrets.token_urlsafe(48),
        ENVIRONMENT="development",
    )
    return env


def cargar_datos(url_base: str, env: dict, n_municipios: int) -> None:
    motor = create_engine(url_base)
    with motor.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    motor.dispose()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, env=env, check=True, capture_output=True,
    )

    sys.path.insert(0, str(RAIZ))
    os.environ.update(env)
    from app.api.roles import ROL_ADMIN
    from app.core.security import hash_password

    motor = create_engine(url_base)
    with motor.begin() as c:
        c.execute(text(
            "INSERT INTO departamentos (nombre) "
            "SELECT 'Departamento simulado ' || g FROM generate_series(1, 9) g"
        ))
        c.execute(text("INSERT INTO enfermedades (nombre) VALUES ('dengue'), ('malaria')"))
        c.execute(text(
            "INSERT INTO municipios (nombre, departamento_id, geometria) "
            "SELECT 'Municipio simulado ' || g, 1 + (g % 9), "
            "  ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint("
            "    -69.0 + (g % 25) * 0.4, -22.0 + (g / 25) * 0.4), 4326), "
            f"    0.15, 'quad_segs={VERTICES_POR_CUADRANTE}')) "
            "FROM generate_series(1, :n) g"
        ), {"n": n_municipios})
        c.execute(text(
            "INSERT INTO modelos (nombre, version, fecha_entrenamiento, metricas_entrenamiento) "
            "VALUES ('modelo simulado', 'carga', now(), '{}'::jsonb)"
        ))
        # 8 semanas de historial por (municipio, enfermedad): la consulta de
        # "prediccion vigente" tiene que descartar las 7 anteriores.
        c.execute(text(
            "INSERT INTO predicciones (municipio_id, enfermedad_id, modelo_id, "
            "  fecha_generacion, fecha_estimada_riesgo, nivel_riesgo, "
            "  probabilidad_pct, nivel_confianza, variables_explicativas) "
            "SELECT m.id, e.id, (SELECT min(id) FROM modelos), "
            "  now() - (s * interval '7 days'), "
            "  ((now() - (s * interval '7 days')) AT TIME ZONE 'UTC')::date + 21 + (m.id % 8), "
            "  CASE WHEN p >= 70 THEN 'alto' WHEN p >= 40 THEN 'medio' ELSE 'bajo' END, "
            "  p, 'medio', "
            "  '[{\"variable\": \"precipitacion_mm\", \"peso\": 0.4}, "
            "{\"variable\": \"temperatura_media_c\", \"peso\": 0.3}]'::jsonb "
            "FROM municipios m CROSS JOIN enfermedades e CROSS JOIN generate_series(0, 7) s "
            "CROSS JOIN LATERAL (SELECT ((m.id * 37 + e.id * 11 + s * 5) % 100)::numeric AS p) q"
        ))
        rol_id = c.execute(
            text("INSERT INTO roles (nombre) VALUES (:n) RETURNING id"), {"n": ROL_ADMIN}
        ).scalar_one()
        c.execute(
            text("INSERT INTO usuarios (email, password_hash, rol_id) VALUES (:e, :h, :r)"),
            {"e": EMAIL, "h": hash_password(PASSWORD), "r": rol_id},
        )
    motor.dispose()


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def levantar_api(env: dict, puerto: int) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(puerto),
         "--workers", "1", "--log-level", "warning"],
        cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            if httpx.get(f"http://127.0.0.1:{puerto}/health", timeout=2).status_code == 200:
                return proc
        except httpx.HTTPError:
            time.sleep(0.5)
    proc.terminate()
    sys.exit("La API no arranco.")


def percentil(valores: list[float], p: float) -> float:
    orden = sorted(valores)
    return orden[min(len(orden) - 1, round(p / 100 * (len(orden) - 1)))]


def medir(url: str, token: str, concurrencia: int, duracion: float) -> dict:
    cabeceras = {"Authorization": f"Bearer {token}"}
    fin = time.perf_counter() + duracion

    def trabajador(_):
        tiempos, errores, tam = [], 0, 0
        with httpx.Client(headers=cabeceras, timeout=30) as cliente:
            while time.perf_counter() < fin:
                t0 = time.perf_counter()
                r = cliente.get(url)
                dt = time.perf_counter() - t0
                if r.status_code == 200:
                    tiempos.append(dt)
                    tam = len(r.content)
                else:
                    errores += 1
        return tiempos, errores, tam

    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        partes = list(pool.map(trabajador, range(concurrencia)))
    tiempos = [t for p in partes for t in p[0]]
    return {
        "concurrencia": concurrencia,
        "peticiones_ok": len(tiempos),
        "errores": sum(p[1] for p in partes),
        "peticiones_por_s": round(len(tiempos) / duracion, 1),
        "p50_ms": round(statistics.median(tiempos) * 1000),
        "p95_ms": round(percentil(tiempos, 95) * 1000),
        "p99_ms": round(percentil(tiempos, 99) * 1000),
        "max_ms": round(max(tiempos) * 1000),
        "respuesta_kb": round(max(p[2] for p in partes) / 1024),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--admin-url", required=True, help="URL de la base 'postgres' LOCAL")
    ap.add_argument("--municipios", type=int, default=350)
    ap.add_argument("--duracion", type=float, default=20, help="segundos por nivel")
    ap.add_argument("--niveles", default="1,5,10,25", help="concurrencias, separadas por coma")
    ap.add_argument("--umbral-ms", type=int, default=2000)
    args = ap.parse_args()

    verificar_local(args.admin_url)
    url_base = url_con_base(args.admin_url, BASE_TEMPORAL)
    env = entorno(url_base)
    api = None
    try:
        print(f"Creando base temporal {BASE_TEMPORAL} y cargando {args.municipios} municipios simulados...")
        crear_base(args.admin_url)
        cargar_datos(url_base, env, args.municipios)
        puerto = puerto_libre()
        api = levantar_api(env, puerto)
        base = f"http://127.0.0.1:{puerto}"
        login = httpx.post(f"{base}/auth/login", data={"username": EMAIL, "password": PASSWORD})
        login.raise_for_status()
        token = login.json()["access_token"]

        url = f"{base}/zonas/riesgo"
        n = len(httpx.get(url, headers={"Authorization": f"Bearer {token}"}).json())
        print(f"GET /zonas/riesgo devuelve {n} filas (municipio x enfermedad).")
        for _ in range(5):  # calentamiento
            httpx.get(url, headers={"Authorization": f"Bearer {token}"})

        resultados = []
        for nivel in (int(x) for x in args.niveles.split(",")):
            r = medir(url, token, nivel, args.duracion)
            resultados.append(r)
            print(json.dumps(r))
        peor = max(r["p95_ms"] for r in resultados)
        cumple = peor < args.umbral_ms and all(r["errores"] == 0 for r in resultados)
        print(f"\nPeor p95: {peor} ms (umbral {args.umbral_ms} ms) -> {'CUMPLE' if cumple else 'NO CUMPLE'}")
        return 0 if cumple else 1
    finally:
        if api is not None:
            api.terminate()
            api.wait(timeout=10)
        borrar_base(args.admin_url)
        print(f"Base temporal {BASE_TEMPORAL} eliminada.")


if __name__ == "__main__":
    raise SystemExit(main())
