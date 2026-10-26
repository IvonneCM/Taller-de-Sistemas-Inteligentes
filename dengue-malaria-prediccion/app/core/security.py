"""JWT y hashing de contrasenas (TASK-017 / REQ-019, NFR-005).

Este modulo no lee secretos al importarse: las funciones leen las variables
de entorno en cada llamada. Asi los tests pueden definir un SECRET_KEY de
prueba sin depender del orden de importacion. TASK-003 (Ignacio) consolidara
estas variables en app/core/config.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt


ALGORITMO_PERMITIDO = "HS256"
ISSUER_POR_DEFECTO = "dengue-malaria-api"
ACCESS_TOKEN_EXPIRE_MINUTES_POR_DEFECTO = 30
REFRESH_TOKEN_EXPIRE_DAYS_POR_DEFECTO = 7


class TokenError(Exception):
    """Token ausente, invalido, expirado o de un tipo distinto."""


@dataclass(frozen=True)
class RefreshTokenGenerado:
    token: str
    jti: str
    expira_en: datetime


def _secreto() -> str:
    secreto = os.environ.get("SECRET_KEY")
    if not secreto:
        raise RuntimeError(
            "SECRET_KEY no esta definida. Configurar una clave larga y "
            "aleatoria en el entorno (nunca hardcodearla)."
        )
    return secreto


def _algoritmo() -> str:
    algoritmo = os.environ.get("ALGORITHM", ALGORITMO_PERMITIDO).upper()
    if algoritmo != ALGORITMO_PERMITIDO:
        raise RuntimeError(
            f"ALGORITHM={algoritmo!r} no permitido. Usar {ALGORITMO_PERMITIDO}."
        )
    return algoritmo


def _issuer() -> str:
    return os.environ.get("JWT_ISSUER", ISSUER_POR_DEFECTO)


def _entero_env(nombre: str, por_defecto: int) -> int:
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    try:
        numero = int(valor)
    except ValueError as exc:
        raise RuntimeError(f"{nombre} debe ser un entero.") from exc
    if numero <= 0:
        raise RuntimeError(f"{nombre} debe ser mayor que cero.")
    return numero


def segundos_vida_access_token() -> int:
    return _entero_env(
        "ACCESS_TOKEN_EXPIRE_MINUTES", ACCESS_TOKEN_EXPIRE_MINUTES_POR_DEFECTO
    ) * 60


def hash_password(password: str) -> str:
    """Devuelve un hash bcrypt con salt aleatorio."""
    if not password:
        raise ValueError("La contrasena no puede estar vacia.")
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Compara una contrasena contra un hash bcrypt sin lanzar excepciones."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (TypeError, ValueError):
        return False


def _payload_base(usuario_id: int, rol: str, tipo: str) -> dict[str, Any]:
    ahora = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "rol": rol,
        "tipo": tipo,
        "iat": ahora,
        "iss": _issuer(),
    }
    return payload


def crear_access_token(usuario_id: int, rol: str) -> str:
    payload = _payload_base(usuario_id, rol, "access")
    payload["jti"] = uuid4().hex
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=_entero_env(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            ACCESS_TOKEN_EXPIRE_MINUTES_POR_DEFECTO,
        )
    )
    return jwt.encode(payload, _secreto(), algorithm=_algoritmo())


def crear_refresh_token(usuario_id: int, rol: str) -> RefreshTokenGenerado:
    jti = uuid4().hex
    expira_en = datetime.now(timezone.utc) + timedelta(
        days=_entero_env(
            "REFRESH_TOKEN_EXPIRE_DAYS", REFRESH_TOKEN_EXPIRE_DAYS_POR_DEFECTO
        )
    )
    payload = _payload_base(usuario_id, rol, "refresh")
    payload.update({"jti": jti, "exp": expira_en})
    token = jwt.encode(payload, _secreto(), algorithm=_algoritmo())
    return RefreshTokenGenerado(token=token, jti=jti, expira_en=expira_en)


def decodificar_token(token: str, tipo_esperado: str) -> dict[str, Any]:
    """Valida firma, expiracion, issuer y tipo; devuelve el payload."""
    try:
        payload = jwt.decode(
            token,
            _secreto(),
            algorithms=[_algoritmo()],
            options={"require_exp": True},
        )
    except JWTError as exc:
        raise TokenError("Token invalido o expirado.") from exc

    if payload.get("iss") != _issuer():
        raise TokenError("Emisor de token invalido.")
    if payload.get("tipo") != tipo_esperado:
        raise TokenError("Tipo de token invalido.")

    try:
        usuario_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TokenError("Token sin usuario valido.") from exc

    payload["usuario_id"] = usuario_id
    return payload
