"""Verificacion de TASK-035 / H-3: limite de intentos fallidos de login."""

import pytest

from app.core.limite_intentos import LimiteIntentos, limite_login

CLAVE_MALA = "contrasena-equivocada"


class RelojFalso:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


# --- Unidad: el contador ---------------------------------------------------

def test_permite_hasta_el_maximo_y_bloquea_despues():
    reloj = RelojFalso()
    limite = LimiteIntentos(ventana_segundos=900, reloj=reloj)
    for _ in range(4):
        limite.registrar_fallo("email:a")
    assert limite.segundos_de_espera("email:a", 5) == 0
    limite.registrar_fallo("email:a")
    assert limite.segundos_de_espera("email:a", 5) == 900


def test_la_espera_baja_con_el_tiempo_y_se_libera():
    reloj = RelojFalso()
    limite = LimiteIntentos(ventana_segundos=900, reloj=reloj)
    for _ in range(5):
        limite.registrar_fallo("email:a")
    reloj.t += 600
    assert limite.segundos_de_espera("email:a", 5) == 300
    reloj.t += 301
    assert limite.segundos_de_espera("email:a", 5) == 0


def test_las_claves_son_independientes_y_olvidar_las_limpia():
    limite = LimiteIntentos(reloj=RelojFalso())
    for _ in range(5):
        limite.registrar_fallo("email:a")
    assert limite.segundos_de_espera("email:b", 5) == 0
    limite.olvidar("email:a")
    assert limite.segundos_de_espera("email:a", 5) == 0


def test_la_memoria_tiene_tope(monkeypatch):
    monkeypatch.setattr("app.core.limite_intentos._MAX_CLAVES", 3)
    limite = LimiteIntentos(reloj=RelojFalso())
    for i in range(10):
        limite.registrar_fallo(f"email:{i}")
    assert len(limite._fallos) == 3


# --- Integracion: POST /auth/login -----------------------------------------

def _login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


@pytest.fixture()
def usuario(crear_usuario):
    return crear_usuario("limite@prueba.local", "epidemiologo")[0]


def test_cinco_fallos_bloquean_el_sexto_incluso_con_la_clave_correcta(client, usuario):
    for _ in range(5):
        assert _login(client, usuario.email, CLAVE_MALA).status_code == 401
    r = _login(client, usuario.email, "ClaveSegura123!")
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    assert "access_token" not in r.text


def test_un_login_correcto_borra_el_contador_del_correo(client, usuario):
    for _ in range(4):
        _login(client, usuario.email, CLAVE_MALA)
    assert _login(client, usuario.email, "ClaveSegura123!").status_code == 200
    for _ in range(4):
        assert _login(client, usuario.email, CLAVE_MALA).status_code == 401  # parte de cero


def test_el_bloqueo_es_por_correo_otro_usuario_sigue_entrando(client, usuario, crear_usuario):
    otro, clave = crear_usuario("otro@prueba.local", "admin")
    for _ in range(5):
        _login(client, usuario.email, CLAVE_MALA)
    assert _login(client, usuario.email, CLAVE_MALA).status_code == 429
    assert _login(client, otro.email, clave).status_code == 200


def test_correos_inexistentes_tambien_cuentan_y_no_se_distinguen(client):
    for _ in range(5):
        assert _login(client, "no-existe@prueba.local", CLAVE_MALA).status_code == 401
    assert _login(client, "no-existe@prueba.local", CLAVE_MALA).status_code == 429


def test_mayusculas_en_el_correo_no_evaden_el_limite(client, usuario):
    for variante in ("LIMITE@prueba.local", "Limite@Prueba.Local", usuario.email,
                     "limite@PRUEBA.local", "limite@prueba.LOCAL"):
        _login(client, variante, CLAVE_MALA)
    assert _login(client, usuario.email, CLAVE_MALA).status_code == 429


def test_el_limite_por_ip_frena_el_barrido_de_correos(client, monkeypatch):
    monkeypatch.setenv("LOGIN_MAX_INTENTOS_IP", "3")
    from app.core import config
    config.get_settings.cache_clear()
    try:
        for i in range(3):
            assert _login(client, f"x{i}@prueba.local", CLAVE_MALA).status_code == 401
        assert _login(client, "otro-nuevo@prueba.local", CLAVE_MALA).status_code == 429
    finally:
        monkeypatch.undo()
        config.get_settings.cache_clear()


def test_el_limite_se_puede_desactivar(client, usuario, monkeypatch):
    monkeypatch.setenv("LOGIN_MAX_INTENTOS_EMAIL", "0")
    monkeypatch.setenv("LOGIN_MAX_INTENTOS_IP", "0")
    from app.core import config
    config.get_settings.cache_clear()
    try:
        for _ in range(8):
            assert _login(client, usuario.email, CLAVE_MALA).status_code == 401
    finally:
        monkeypatch.undo()
        config.get_settings.cache_clear()


def test_el_estado_del_limite_es_el_de_la_instancia_global(client, usuario):
    _login(client, usuario.email, CLAVE_MALA)
    assert limite_login.segundos_de_espera(f"email:{usuario.email}", 1) > 0
