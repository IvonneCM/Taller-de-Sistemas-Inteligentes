"""Verificacion de TASK-007 / REQ-019, REQ-020: la tabla `usuarios` guarda
solo el hash de la contrasena y ningun dato personal de pacientes.

El hashing en si (bcrypt) es TASK-017 (/auth/login); aqui se fija el esquema
para que nadie agregue despues una columna de contrasena en texto plano o de
datos personales sin que un test falle."""

from app.models import Usuario

COLUMNAS_PROHIBIDAS = {
    "password", "contrasena", "clave", "nombre", "apellido", "ci", "carnet",
    "documento", "direccion", "telefono", "paciente", "historia_clinica",
}


def test_usuarios_guarda_solo_password_hash():
    columnas = {c.name for c in Usuario.__table__.columns}
    assert "password_hash" in columnas
    assert not (columnas & COLUMNAS_PROHIBIDAS), (
        f"REQ-019/REQ-020: columnas no permitidas en usuarios: {columnas & COLUMNAS_PROHIBIDAS}"
    )


def test_password_hash_no_admite_nulos():
    assert Usuario.__table__.columns["password_hash"].nullable is False
