"""Seed de usuarios demo para desarrollo (TASK-017/TASK-018).

No contiene contrasenas ni datos reales. La contrasena se toma de
SEED_DEMO_PASSWORD o se pide por consola; nunca se imprime ni se versiona.
Los emails usan el dominio ficticio @demo.local.

Uso:
    python -m app.etl.seed_usuarios
    python -m app.etl.seed_usuarios --reset-passwords
    python -m app.etl.seed_usuarios --delete
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.etl.seed_catalogo import seed as seed_catalogo
from app.models import Municipio, RefreshToken, Rol, Usuario

DOMINIO_DEMO = "@demo.local"
ROLES = (
    "autoridad",
    "sedes",
    "epidemiologo",
    "coordinador_municipal",
    "admin",
)
USUARIOS_DEMO = (
    ("autoridad@demo.local", "autoridad", None),
    ("sedes@demo.local", "sedes", None),
    ("epidemiologo@demo.local", "epidemiologo", None),
    ("coordinador@demo.local", "coordinador_municipal", "GUAYARAMERIN"),
    ("admin@demo.local", "admin", None),
)


def _verificar_entorno() -> None:
    entorno = os.environ.get("ENVIRONMENT", "development").lower()
    if entorno == "production":
        raise RuntimeError(
            "seed_usuarios no se ejecuta con ENVIRONMENT=production."
        )


def _leer_password() -> str:
    password = os.environ.get("SEED_DEMO_PASSWORD")
    if password:
        return password

    if sys.stdin.isatty():
        password = getpass.getpass(
            "Password para los usuarios demo (no se muestra): "
        )
        if password:
            return password

    raise RuntimeError(
        "Definir SEED_DEMO_PASSWORD o ejecutar en una terminal interactiva."
    )


def _validar_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("SEED_DEMO_PASSWORD debe tener al menos 8 caracteres.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contrasena supera el limite de 72 bytes de bcrypt.")


def seed(
    password: str | None = None,
    *,
    db=None,
    reset_passwords: bool = False,
) -> dict[str, str]:
    """Crea roles y usuarios demo de forma idempotente."""
    _verificar_entorno()
    password = password or _leer_password()
    _validar_password(password)

    propio = db is None
    if propio:
        db = SessionLocal()

    try:
        seed_catalogo(db=db)

        roles = {}
        for nombre in ROLES:
            rol = db.execute(
                select(Rol).where(Rol.nombre == nombre)
            ).scalar_one_or_none()
            if rol is None:
                rol = Rol(nombre=nombre)
                db.add(rol)
            roles[nombre] = rol
        db.flush()

        municipio = db.execute(
            select(Municipio).where(Municipio.nombre == "GUAYARAMERIN")
        ).scalar_one_or_none()
        if municipio is None:
            raise RuntimeError(
                "No se encontro GUAYARAMERIN. Ejecutar seed_catalogo primero."
            )

        resultado: dict[str, str] = {}
        password_hash = hash_password(password)

        for email, nombre_rol, nombre_municipio in USUARIOS_DEMO:
            usuario = db.execute(
                select(Usuario).where(Usuario.email == email)
            ).scalar_one_or_none()
            municipio_id = (
                municipio.id
                if nombre_municipio == "GUAYARAMERIN"
                else None
            )

            if usuario is None:
                db.add(
                    Usuario(
                        email=email,
                        password_hash=password_hash,
                        rol_id=roles[nombre_rol].id,
                        municipio_asignado_id=municipio_id,
                    )
                )
                resultado[email] = "creado"
                continue

            cambios = False
            if usuario.rol_id != roles[nombre_rol].id:
                usuario.rol_id = roles[nombre_rol].id
                cambios = True
            if usuario.municipio_asignado_id != municipio_id:
                usuario.municipio_asignado_id = municipio_id
                cambios = True
            if reset_passwords:
                usuario.password_hash = password_hash
                cambios = True
            resultado[email] = "actualizado" if cambios else "sin_cambios"

        db.flush()
        if propio:
            db.commit()
        return resultado
    except Exception:
        if propio:
            db.rollback()
        raise
    finally:
        if propio:
            db.close()


def delete(*, db=None) -> dict[str, int]:
    """Elimina solo los usuarios demo y sus refresh tokens."""
    _verificar_entorno()

    propio = db is None
    if propio:
        db = SessionLocal()

    try:
        ids_demo = list(
            db.execute(
                select(Usuario.id).where(Usuario.email.like(f"%{DOMINIO_DEMO}"))
            ).scalars()
        )
        if not ids_demo:
            if propio:
                db.commit()
            return {"usuarios": 0, "refresh_tokens": 0}

        tokens = db.execute(
            sql_delete(RefreshToken).where(
                RefreshToken.usuario_id.in_(ids_demo)
            )
        ).rowcount
        usuarios = db.execute(
            sql_delete(Usuario).where(Usuario.id.in_(ids_demo))
        ).rowcount

        if propio:
            db.commit()
        return {
            "usuarios": usuarios or 0,
            "refresh_tokens": tokens or 0,
        }
    except Exception:
        if propio:
            db.rollback()
        raise
    finally:
        if propio:
            db.close()


def _imprimir_resultado(resultado: dict[str, str]) -> None:
    print("Usuarios demo:")
    for email, estado in resultado.items():
        print(f"  {email}: {estado}")
    print("Password: definida por SEED_DEMO_PASSWORD (no se imprime).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Elimina los usuarios @demo.local y sus refresh tokens.",
    )
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="Actualiza el hash de los usuarios demo existentes.",
    )
    args = parser.parse_args()

    if args.delete:
        resultado = delete()
        print(
            "Eliminados: "
            f"{resultado['usuarios']} usuarios demo, "
            f"{resultado['refresh_tokens']} refresh tokens."
        )
        return

    _imprimir_resultado(seed(reset_passwords=args.reset_passwords))


if __name__ == "__main__":
    main()
