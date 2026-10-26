"""Dependencias de autenticacion y RBAC (TASK-017/TASK-018 / REQ-019)."""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import TokenError, decodificar_token
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Devuelve el usuario autenticado leyendo su rol actual desde la BD."""
    try:
        payload = decodificar_token(token, "access")
    except TokenError:
        raise _credenciales_invalidas()

    usuario = db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.id == payload["usuario_id"])
    ).scalar_one_or_none()

    if usuario is None:
        raise _credenciales_invalidas()
    return usuario


def require_role(*roles: str) -> Callable[..., Usuario]:
    """Dependencia que exige que el usuario tenga uno de los roles dados.

    No hay bypass implicito para admin: cada endpoint declara la lista exacta
    de roles permitidos.
    """
    roles_permitidos = frozenset(roles)

    def dependency(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if (
            current_user.rol is None
            or current_user.rol.nombre not in roles_permitidos
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para este recurso",
            )
        return current_user

    return dependency
