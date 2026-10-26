"""Verificacion de TASK-040 (NFR-003): 'tests con la base caida y con entrada
invalida; los logs muestran el error sin datos sensibles'."""

import logging

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core import observabilidad
from app.core.config import get_settings
from app.core.database import engine, get_db
from app.core.security import crear_access_token
from app.main import app

SECRETO = "ClaveSecretaQueNoDebeVerseNunca"


@pytest.fixture()
def sesion_sin_base():
    """Sesion contra un puerto sin servidor: simula la base caida."""
    motor = create_engine(
        "postgresql://u:p@127.0.0.1:1/x",
        connect_args={"connect_timeout": 1},
        hide_parameters=True,
    )
    sesion = sessionmaker(bind=motor)()
    yield sesion
    sesion.close()
    motor.dispose()


def _con_base_caida(sesion):
    def _dependencia():
        yield sesion

    return _dependencia


def _app_de_prueba() -> FastAPI:
    """App minima con el mismo middleware y manejadores que la real."""
    pequena = FastAPI()
    observabilidad.instalar(pequena)

    @pequena.get("/falla")
    def falla():
        raise RuntimeError(f"detalle interno {SECRETO}")

    @pequena.get("/lenta")
    def lenta(db: Session = Depends(get_db)):
        db.execute(text("SET LOCAL statement_timeout = '200ms'"))
        db.execute(text("SELECT pg_sleep(2)"))
        return {"ok": True}

    return pequena


def test_health_es_liveness_y_no_consulta_la_base(client, sesion_sin_base):
    app.dependency_overrides[get_db] = _con_base_caida(sesion_sin_base)
    assert client.get("/health").json() == {"status": "ok"}


def test_health_ready_ok_con_la_base_disponible(client):
    respuesta = client.get("/health/ready")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "database": "ok"}


def test_health_ready_responde_503_si_la_base_no_responde(client, sesion_sin_base):
    app.dependency_overrides[get_db] = _con_base_caida(sesion_sin_base)

    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "degraded", "database": "unavailable"}
    assert respuesta.headers["retry-after"] == "5"


def test_endpoint_con_la_base_caida_responde_503_sin_filtrar_detalles(
    client, sesion_sin_base
):
    app.dependency_overrides[get_db] = _con_base_caida(sesion_sin_base)
    cabecera = {"Authorization": f"Bearer {crear_access_token(1, 'admin')}"}

    respuesta = client.get("/zonas/riesgo", headers=cabecera)

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert "no esta disponible" in cuerpo["detail"]
    assert cuerpo["request_id"] == respuesta.headers["x-request-id"]
    assert respuesta.headers["retry-after"] == "5"
    texto = respuesta.text
    assert "127.0.0.1" not in texto and "postgresql" not in texto and "psycopg" not in texto


def test_una_consulta_lenta_se_corta_y_responde_503(db_session):
    pequena = _app_de_prueba()
    pequena.dependency_overrides[get_db] = lambda: db_session

    respuesta = TestClient(pequena).get("/lenta")

    assert respuesta.status_code == 503
    assert "no esta disponible" in respuesta.json()["detail"]


def test_la_conexion_usa_los_timeouts_configurados(db_session):
    ajustes = get_settings()
    assert db_session.execute(text("SHOW statement_timeout")).scalar() == (
        f"{ajustes.DB_STATEMENT_TIMEOUT_MS // 1000}s"
    )
    assert engine.pool.timeout() == ajustes.DB_POOL_TIMEOUT_SECONDS


def test_el_limite_de_consulta_no_usa_parametros_de_arranque_que_los_pooler_rechazan():
    """Neon y PgBouncer rechazan `options=-c ...` con "unsupported startup parameter":
    con eso la API desplegada no podia conectarse (regresion encontrada en Render)."""
    import inspect

    from app.core import database

    fuente = inspect.getsource(database)
    assert '"options"' not in fuente and "'options'" not in fuente
    assert "SET LOCAL statement_timeout" in fuente


def test_el_limite_aplica_en_cada_transaccion_y_se_puede_desactivar(monkeypatch):
    from app.core import database

    with engine.connect() as conexion:
        with conexion.begin():
            assert conexion.execute(text("SHOW statement_timeout")).scalar() == "15s"
    monkeypatch.setattr(database._settings, "DB_STATEMENT_TIMEOUT_MS", 0)
    with engine.connect() as conexion:
        with conexion.begin():
            assert conexion.execute(text("SHOW statement_timeout")).scalar() == "0"


def test_error_no_previsto_responde_500_generico_y_deja_la_traza_en_el_log(caplog):
    caplog.set_level(logging.INFO)
    cliente = TestClient(_app_de_prueba(), raise_server_exceptions=False)

    respuesta = cliente.get("/falla")

    assert respuesta.status_code == 500
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == "Error interno del servidor."
    assert cuerpo["request_id"] == respuesta.headers["x-request-id"]
    # La respuesta no revela nada interno...
    assert SECRETO not in respuesta.text and "RuntimeError" not in respuesta.text
    # ...pero el log del servidor si tiene la traza y el identificador.
    registros = [r for r in caplog.records if r.name == "app.http"]
    assert any("Error no controlado en GET /falla" in r.getMessage() for r in registros)
    assert any(r.exc_info for r in registros)
    assert all(getattr(r, "request_id", None) == cuerpo["request_id"] for r in registros)


def test_se_conserva_un_request_id_valido_y_se_reemplaza_uno_invalido(client):
    propio = client.get("/health", headers={"X-Request-ID": "demo-123.abc"})
    assert propio.headers["x-request-id"] == "demo-123.abc"

    for invalido in ("con espacios y {llaves}", "x" * 65):
        respuesta = client.get("/health", headers={"X-Request-ID": invalido})
        generado = respuesta.headers["x-request-id"]
        assert generado != invalido and len(generado) == 32


def test_cada_respuesta_trae_un_request_id_distinto(client):
    primero = client.get("/health").headers["x-request-id"]
    segundo = client.get("/health").headers["x-request-id"]
    assert primero != segundo


def test_la_validacion_422_no_devuelve_lo_enviado(client):
    # Con credenciales inexistentes es 401; para forzar 422 se omite el campo.
    sin_password = client.post("/auth/login", data={"username": "alguien@demo.local"})

    assert sin_password.status_code == 422
    cuerpo = sin_password.json()
    assert cuerpo["request_id"] == sin_password.headers["x-request-id"]
    assert cuerpo["detail"]
    for error in cuerpo["detail"]:
        assert set(error) == {"loc", "msg", "type"}


def test_los_logs_registran_la_peticion_sin_secretos(client, caplog):
    caplog.set_level(logging.INFO)
    client.post("/auth/login", data={"username": "alguien@demo.local", "password": SECRETO})
    client.get(f"/zonas/riesgo?enfermedad_id=1&token={SECRETO}")

    # Solo los logs de la API (el cliente de pruebas, httpx, imprime la URL completa).
    registros = [r for r in caplog.records if r.name.startswith("app")]
    texto = "\n".join(r.getMessage() for r in registros)
    assert "POST /auth/login -> 401" in texto
    assert "GET /zonas/riesgo -> 401" in texto
    assert SECRETO not in texto
    assert "alguien@demo.local" not in texto
    niveles = {
        r.getMessage().split(" -> ")[0]: r.levelno
        for r in registros if " -> " in r.getMessage()
    }
    assert niveles["POST /auth/login"] == logging.WARNING  # 4xx se registra como aviso


def test_configure_logging_es_idempotente():
    raiz = logging.getLogger()
    observabilidad.configure_logging("INFO")
    antes = len([h for h in raiz.handlers if getattr(h, "_observabilidad_handler", False)])
    observabilidad.configure_logging("INFO")
    despues = len([h for h in raiz.handlers if getattr(h, "_observabilidad_handler", False)])
    assert antes == despues == 1
