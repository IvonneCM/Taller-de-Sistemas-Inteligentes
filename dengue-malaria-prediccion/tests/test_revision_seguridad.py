"""Verificacion de TASK-035: cada control de la revision de seguridad detecta lo
que debe detectar (se prueba que FALLA cuando corresponde, no solo que pasa)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.core import revision_seguridad as rs
from app.core.security import hash_password
from app.models import Alerta, Modelo, Prediccion, Rol, Usuario
from tests.api.helpers import crear_modelo, crear_prediccion


@pytest.fixture()
def conexion(db_session):
    return db_session.connection()


# ------------------------------------------------------------ REQ-020: sin PII

def test_el_esquema_actual_no_tiene_datos_personales(conexion):
    r = rs.sin_datos_personales(conexion)
    assert r.estado == rs.OK and "usuarios.email" in r.detalle


@pytest.mark.parametrize("columna", ["telefono", "nombre_paciente", "ci", "fecha_nacimiento", "direccion_domicilio"])
def test_detecta_una_columna_de_datos_personales(db_session, conexion, columna):
    db_session.execute(text(f'CREATE TABLE prueba_pii ("{columna}" text)'))  # DDL transaccional: se revierte
    r = rs.sin_datos_personales(conexion)
    assert r.estado == rs.FALLA and f"prueba_pii.{columna}" in r.detalle


def test_no_marca_como_pii_columnas_legitimas(db_session, conexion):
    db_session.execute(text('CREATE TABLE prueba_ok (casos int, "ciclo" text, "decimal" int)'))
    assert rs.sin_datos_personales(conexion).estado == rs.OK


# ------------------------------------------------------- REQ-005: alertas

@pytest.fixture()
def prediccion(db_session, catalogo):
    dengue = catalogo["enfermedades"]["dengue"]
    return crear_prediccion(db_session, municipio=catalogo["municipios"]["GUAYARAMERIN"],
                            enfermedad=dengue, modelo=crear_modelo(db_session, dengue))


def test_sin_alertas_o_con_alertas_completas_pasa(db_session, conexion, prediccion):
    assert rs.alertas_con_justificacion(conexion).estado == rs.OK
    db_session.add(Alerta(prediccion_id=prediccion.id, umbral_aplicado=70, justificacion="Casos en alza."))
    db_session.flush()
    r = rs.alertas_con_justificacion(conexion)
    assert r.estado == rs.OK and "1 alertas" in r.detalle


def test_detecta_una_alerta_sin_justificacion_aunque_la_base_ya_lo_impida(db_session, conexion, prediccion):
    # La restriccion de la base es la primera barrera; el control es la segunda.
    db_session.execute(text("ALTER TABLE alertas DROP CONSTRAINT ck_alerta_justificacion_no_vacia"))
    db_session.add(Alerta(prediccion_id=prediccion.id, umbral_aplicado=70, justificacion="   "))
    db_session.flush()
    r = rs.alertas_con_justificacion(conexion)
    assert r.estado == rs.FALLA and "1 sin justificacion" in r.detalle


def test_detecta_una_alerta_cuya_prediccion_no_tiene_variables(db_session, conexion, prediccion):
    db_session.execute(text("UPDATE predicciones SET variables_explicativas = '[]'::jsonb WHERE id = :i"), {"i": prediccion.id})
    db_session.add(Alerta(prediccion_id=prediccion.id, umbral_aplicado=70, justificacion="Texto cualquiera."))
    db_session.flush()
    r = rs.alertas_con_justificacion(conexion)
    assert r.estado == rs.FALLA and "1 sin variables" in r.detalle


# ------------------------------------------------------ NFR-005: contrasenas

def _usuario(db, email, password_hash, rol="admin"):
    r = db.query(Rol).filter_by(nombre=rol).first() or Rol(nombre=rol)
    db.add(r)
    db.flush()
    db.execute(text("INSERT INTO usuarios (email, password_hash, rol_id) VALUES (:e, :h, :r)"),
               {"e": email, "h": password_hash, "r": r.id})  # SQL directo: se salta la validacion del modelo


def test_contrasenas_con_bcrypt_pasan(db_session, conexion):
    _usuario(db_session, "a@demo.local", hash_password("ClaveSegura123!"))
    assert rs.contrasenas_con_hash(conexion).estado == rs.OK


def test_detecta_una_contrasena_en_texto_plano(db_session, conexion):
    _usuario(db_session, "a@demo.local", hash_password("ClaveSegura123!"))
    _usuario(db_session, "b@demo.local", "contrasena-en-texto-plano")
    r = rs.contrasenas_con_hash(conexion)
    assert r.estado == rs.FALLA and "1 de 2" in r.detalle


# --------------------------------------------------- NFR-009: inmutabilidad

def test_el_codigo_real_no_modifica_predicciones():
    assert rs.predicciones_inmutables().estado == rs.OK


@pytest.mark.parametrize("codigo", [
    "db.execute(update(Prediccion).values(nivel_riesgo='bajo'))",
    'db.execute(text("UPDATE predicciones SET nivel_riesgo = 1"))',
    "db.query(Prediccion).delete()",
    'conn.execute("DELETE FROM predicciones")',
])
def test_detecta_codigo_que_modifica_o_borra_predicciones(codigo):
    r = rs.predicciones_inmutables({"app/servicio.py": codigo, "app/otro.py": "x = 1"})
    assert r.estado == rs.FALLA and "app/servicio.py" in r.detalle and "app/otro.py" not in r.detalle


# ------------------------------------------------------------ configuracion

@pytest.mark.parametrize("entorno, estado", [
    ({"SECRET_KEY": "a" * 40}, rs.OK),
    ({"SECRET_KEY": "corta"}, rs.AVISO),
    ({"SECRET_KEY": "cambiar-por-una-clave-larga-y-aleatoria"}, rs.AVISO),
    ({"SECRET_KEY": "corta", "ENVIRONMENT": "production"}, rs.FALLA),
    ({"SECRET_KEY": "a" * 40, "ALGORITHM": "none"}, rs.FALLA),
    ({}, rs.AVISO),
])
def test_configuracion_segura(entorno, estado):
    assert rs.configuracion_segura(entorno).estado == estado


# ------------------------------------------------------------- repositorio

def test_el_repositorio_actual_no_tiene_secretos():
    archivos = rs.archivos_versionados()
    if archivos is None:
        pytest.skip("git no disponible")
    r = rs.secretos_en_el_repositorio(archivos)
    assert r.estado == rs.OK, r.detalle


@pytest.mark.parametrize("ruta, contenido, fragmento", [
    ("dengue/.env", "X=1", "archivo de entorno versionado"),
    ("clave.pem", "-----BEGIN RSA PRIVATE KEY-----\nabc", "clave privada"),
    ("aws.txt", "key=AKIAABCDEFGHIJKLMNOP", "AWS"),
    ("db.md", "postgresql://app:Zq8vK2mP9xLw@db.interno:5432/x", "URL de base de datos"),
    ("cfg.py", 'SECRET_KEY = "f3a9c1d2e4b5a6978877665544332211aabbccdd"', "SECRET_KEY con valor real"),
])
def test_detecta_secretos(ruta, contenido, fragmento):
    r = rs.secretos_en_el_repositorio({ruta: contenido})
    assert r.estado == rs.FALLA and fragmento in r.detalle


@pytest.mark.parametrize("contenido", [
    "postgresql://postgres:postgres@localhost:5432/x",
    "postgresql://postgres:test@localhost:55432/x",
    "postgresql://u:p@127.0.0.1:1/x",
    "postgresql://postgres:cambiar-esta-clave@localhost:5433/x",
    "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/x",
    "SECRET_KEY=cambiar-por-una-clave-larga-y-aleatoria",
    "SECRET_KEY=ci-solo-para-pruebas-clave-de-mas-de-32-caracteres",
])
def test_no_marca_claves_de_ejemplo(contenido):
    assert rs.secretos_en_el_repositorio({"doc.md": contenido}).estado == rs.OK


def test_el_env_example_si_puede_estar_versionado():
    assert rs.secretos_en_el_repositorio({"app/.env.example": "A=1"}).estado == rs.OK


# -------------------------------------------------------------------- HTTPS

def test_sin_despliegue_no_se_da_por_verificado():
    r = rs.https_en_despliegue(None)
    assert r.estado == rs.NO_VERIFICADO and "TASK-004" in r.detalle


def test_una_url_http_falla():
    assert rs.https_en_despliegue("http://app.example.com").estado == rs.FALLA


def _respuesta(estado, cabeceras):
    r = MagicMock()
    r.status, r.headers = estado, cabeceras
    r.__enter__.return_value = r
    return r


def test_https_con_hsts_pasa_y_sin_hsts_avisa():
    with patch("urllib.request.urlopen", return_value=_respuesta(200, {"Strict-Transport-Security": "max-age=31536000"})):
        assert rs.https_en_despliegue("https://app.example.com").estado == rs.OK
    with patch("urllib.request.urlopen", return_value=_respuesta(200, {})):
        assert rs.https_en_despliegue("https://app.example.com").estado == rs.AVISO


def test_un_certificado_invalido_o_un_servidor_caido_falla():
    import ssl
    with patch("urllib.request.urlopen", side_effect=ssl.SSLCertVerificationError("certificado vencido")):
        r = rs.https_en_despliegue("https://app.example.com")
    assert r.estado == rs.FALLA and "certificado vencido" in r.detalle


# ----------------------------------------------------------------------- CLI

def test_el_comando_sale_con_codigo_0_si_no_hay_fallas_y_1_si_las_hay(capsys):
    assert rs.main([]) == 0
    assert "HTTPS en el despliegue" in capsys.readouterr().out
    assert rs.main(["--url", "http://inseguro.example.com"]) == 1


# ------------------------------------------- documentacion de la API en produccion

def _rutas_publicas(entorno: str) -> list[str]:
    import json
    import os
    import subprocess
    import sys

    codigo = ("import json; from app.main import app; "
              "print(json.dumps(sorted({'/docs','/redoc','/openapi.json'} & {r.path for r in app.routes})))")
    env = {**os.environ, "ENVIRONMENT": entorno, "SECRET_KEY": "k" * 48}
    salida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, check=True).stdout
    return json.loads(salida.strip().splitlines()[-1])


def test_en_produccion_no_se_publica_la_documentacion_de_la_api():
    assert _rutas_publicas("production") == []


def test_en_desarrollo_la_documentacion_sigue_disponible():
    assert _rutas_publicas("development") == ["/docs", "/openapi.json", "/redoc"]
