"""Prueba de humo del despliegue (TASK-039).

Verifica contra una URL real que la API esta viva, que la base responde y que
el flujo minimo funciona (login -> zonas -> casos). Solo usa la libreria
estandar, para poder correrse desde cualquier maquina sin instalar nada.

    SMOKE_URL=https://mi-app.example.com \\
    SMOKE_EMAIL=autoridad@demo.local SMOKE_PASSWORD=... \\
    python scripts/smoke_test.py

Sale con codigo 0 si todo pasa y 1 si algo falla (imprime cual). La
contrasena se lee del entorno y nunca se imprime."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "10"))


def _pedir(base: str, ruta: str, *, datos: dict | None = None, token: str | None = None):
    cuerpo = urllib.parse.urlencode(datos).encode() if datos is not None else None
    peticion = urllib.request.Request(base + ruta, data=cuerpo)
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=TIMEOUT) as respuesta:
            return respuesta.status, json.loads(respuesta.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, str(getattr(error, "reason", error))


def _verificar(nombre: str, condicion: bool, detalle: str = "") -> bool:
    print(f"[{'OK' if condicion else 'FALLO'}] {nombre}" + (f" ({detalle})" if detalle and not condicion else ""))
    return condicion


def main() -> int:
    base = os.environ.get("SMOKE_URL", "http://127.0.0.1:8000").rstrip("/")
    email = os.environ.get("SMOKE_EMAIL")
    password = os.environ.get("SMOKE_PASSWORD")
    print(f"Prueba de humo contra {base}")

    estado, cuerpo = _pedir(base, "/health")
    if not _verificar("GET /health responde 200", estado == 200 and cuerpo == {"status": "ok"}, f"estado={estado} {cuerpo}"):
        print("La API no responde: no se continua.")
        return 1
    estado, cuerpo = _pedir(base, "/health/ready")
    todo_ok = _verificar("GET /health/ready (la base responde)", estado == 200, f"estado={estado}")

    estado, _ = _pedir(base, "/zonas/riesgo")
    todo_ok &= _verificar("Sin token, /zonas/riesgo responde 401", estado == 401, f"estado={estado}")

    if not (email and password):
        print("Sin SMOKE_EMAIL/SMOKE_PASSWORD: se omite el recorrido autenticado.")
        return 0 if todo_ok else 1

    estado, cuerpo = _pedir(base, "/auth/login", datos={"username": email, "password": password})
    token = (cuerpo or {}).get("access_token")
    todo_ok &= _verificar("POST /auth/login devuelve un token", estado == 200 and bool(token), f"estado={estado}")
    if not token:
        return 1

    estado, zonas = _pedir(base, "/zonas/riesgo", token=token)
    todo_ok &= _verificar("GET /zonas/riesgo con token", estado == 200 and isinstance(zonas, list), f"estado={estado}")
    todo_ok &= _verificar("Hay zonas con prediccion", bool(zonas), "lista vacia: falta cargar los datos de demostracion")
    estado, casos = _pedir(base, "/casos/resumen", token=token)
    todo_ok &= _verificar("GET /casos/resumen con token", estado == 200 and isinstance(casos, list), f"estado={estado}")
    if zonas:
        estado, detalle = _pedir(base, f"/zonas/{zonas[0]['municipio_id']}/prediccion", token=token)
        todo_ok &= _verificar("GET /zonas/{id}/prediccion", estado == 200 and bool(detalle), f"estado={estado}")

    print("RESULTADO: " + ("todo correcto" if todo_ok else "hay fallos"))
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
