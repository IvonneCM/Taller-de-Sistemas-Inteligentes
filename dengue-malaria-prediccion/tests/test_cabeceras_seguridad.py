"""Verificacion de TASK-035 / H-4 y H-9: cabeceras de seguridad de la API."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import cabeceras_seguridad
from app.core.config import get_settings


def _app(entorno, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", entorno)
    get_settings.cache_clear()
    app = FastAPI()
    cabeceras_seguridad.instalar(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.post("/auth/login")
    def login():
        return {"token": "x"}

    return TestClient(app)


def test_toda_respuesta_lleva_las_cabeceras_base(client):
    for ruta in ("/health", "/zonas/riesgo", "/no-existe"):  # 200, 401 y 404
        r = client.get(ruta)
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "no-referrer"


def test_en_desarrollo_no_hay_hsts_ni_csp(client):
    r = client.get("/health")
    assert "Strict-Transport-Security" not in r.headers
    assert "Content-Security-Policy" not in r.headers


def test_en_produccion_hay_hsts_y_csp_cerrada(monkeypatch):
    try:
        r = _app("production", monkeypatch).get("/ok")
        assert "max-age=31536000" in r.headers["Strict-Transport-Security"]
        assert r.headers["Content-Security-Policy"].startswith("default-src 'none'")
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


def test_las_respuestas_de_auth_no_se_guardan_en_cache(monkeypatch):
    try:
        cliente = _app("development", monkeypatch)
        assert cliente.post("/auth/login").headers["Cache-Control"] == "no-store"
        assert "Cache-Control" not in cliente.get("/ok").headers
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


def test_los_errores_del_servidor_tambien_llevan_las_cabeceras(client, monkeypatch):
    from app.main import app

    @app.get("/_falla_para_prueba")
    def falla():
        raise RuntimeError("fallo")

    try:
        r = TestClient(app, raise_server_exceptions=False).get("/_falla_para_prueba")
        assert r.status_code == 500
        assert r.headers["X-Content-Type-Options"] == "nosniff"
    finally:
        app.router.routes[:] = [x for x in app.router.routes if getattr(x, "path", "") != "/_falla_para_prueba"]
