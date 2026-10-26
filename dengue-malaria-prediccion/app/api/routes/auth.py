"""Endpoints de autenticacion (TASK-017 / REQ-019, SEG-01)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import (
    TokenError,
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    hash_password,
    segundos_vida_access_token,
    verify_password,
)
from app.models import RefreshToken, Usuario
from app.schemas.auth import RefreshTokenRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash de relleno para que un email inexistente tarde lo mismo que una
# contrasena incorrecta y no permita enumerar usuarios por tiempo.
_HASH_RELLENO = hash_password("contrasena-de-relleno-no-real")


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _buscar_usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(func.lower(Usuario.email) == email.lower())
    ).scalar_one_or_none()


def _buscar_usuario_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.id == usuario_id)
    ).scalar_one_or_none()


def _emitir_par_tokens(db: Session, usuario: Usuario) -> TokenPair:
    if usuario.rol is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin rol asignado",
        )

    rol = usuario.rol.nombre
    access_token = crear_access_token(usuario.id, rol)
    refresh = crear_refresh_token(usuario.id, rol)
    db.add(
        RefreshToken(
            jti=refresh.jti,
            usuario_id=usuario.id,
            expira_en=refresh.expira_en,
        )
    )
    db.commit()
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh.token,
        expires_in=segundos_vida_access_token(),
    )


@router.post("/login", response_model=TokenPair)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenPair:
    email = form_data.username.strip()
    usuario = _buscar_usuario_por_email(db, email)

    if usuario is None:
        verify_password(form_data.password, _HASH_RELLENO)
        raise _credenciales_invalidas()

    if not verify_password(form_data.password, usuario.password_hash):
        raise _credenciales_invalidas()

    return _emitir_par_tokens(db, usuario)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenPair:
    try:
        payload = decodificar_token(body.refresh_token, "refresh")
    except TokenError:
        raise _credenciales_invalidas()

    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise _credenciales_invalidas()

    registro = db.execute(
        select(RefreshToken)
        .where(RefreshToken.jti == jti)
        .with_for_update()
    ).scalar_one_or_none()
    ahora = datetime.now(timezone.utc)

    if (
        registro is None
        or registro.usuario_id != payload["usuario_id"]
        or registro.revocado_en is not None
        or registro.expira_en <= ahora
    ):
        raise _credenciales_invalidas()

    usuario = _buscar_usuario_por_id(db, payload["usuario_id"])
    if usuario is None:
        raise _credenciales_invalidas()

    registro.revocado_en = ahora
    return _emitir_par_tokens(db, usuario)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> Response:
    """Revoca el refresh token. Responde 204 aunque el token ya no sea valido."""
    try:
        payload = decodificar_token(body.refresh_token, "refresh")
        jti = payload.get("jti")
    except TokenError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if not isinstance(jti, str):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    registro = db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    ).scalar_one_or_none()
    if registro is not None and registro.revocado_en is None:
        registro.revocado_en = datetime.now(timezone.utc)
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
