"""El script de humo (TASK-039) funciona contra un servidor real: se levanta
uvicorn en un hilo con la base de pruebas y se ejecuta el script."""

import importlib.util
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from app.etl.seed_demo import sembrar_demo

RUTA = Path(__file__).resolve().parents[2] / "scripts" / "smoke_test.py"
CLAVE = "ClaveDeDemo-2026"


def _cargar_script():
    especificacion = importlib.util.spec_from_file_location("smoke_test", RUTA)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def servidor(db_session):
    from app.core.database import get_db
    from app.main import app

    sembrar_demo(password=CLAVE, db=db_session)
    # Hilos distintos no pueden compartir la sesion transaccional: se sirve la misma
    # conexion (una a la vez) con un candado.
    candado = threading.Lock()

    def dependencia():
        with candado:
            yield db_session

    app.dependency_overrides[get_db] = dependencia
    puerto = _puerto_libre()
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning"))
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{puerto}"
    servidor.should_exit = True
    hilo.join(timeout=5)
    app.dependency_overrides.clear()


def test_el_script_de_humo_pasa_contra_un_servidor_real(servidor, monkeypatch, capsys):
    monkeypatch.setenv("SMOKE_URL", servidor)
    monkeypatch.setenv("SMOKE_EMAIL", "autoridad@demo.local")
    monkeypatch.setenv("SMOKE_PASSWORD", CLAVE)

    codigo = _cargar_script().main()

    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "FALLO" not in salida and CLAVE not in salida
    assert "todo correcto" in salida


def test_el_script_falla_con_codigo_1_si_la_api_no_responde(monkeypatch, capsys):
    monkeypatch.setenv("SMOKE_URL", f"http://127.0.0.1:{_puerto_libre()}")
    monkeypatch.setenv("SMOKE_TIMEOUT", "1")

    assert _cargar_script().main() == 1
    assert "FALLO" in capsys.readouterr().out


def test_el_script_falla_si_las_credenciales_son_incorrectas(servidor, monkeypatch, capsys):
    monkeypatch.setenv("SMOKE_URL", servidor)
    monkeypatch.setenv("SMOKE_EMAIL", "autoridad@demo.local")
    monkeypatch.setenv("SMOKE_PASSWORD", "incorrecta")

    assert _cargar_script().main() == 1
    assert "incorrecta" not in capsys.readouterr().out
