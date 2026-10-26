"""Dependencias de autenticacion y RBAC de la API (REQ-007, REQ-019).

Alcance: este modulo SOLO verifica un JWT de acceso ya emitido y aplica el
control por rol. Emitir los tokens (`/auth/login`, refresh, bcrypt) es
TASK-017 y el resto del RBAC (`require_role` ampliado, seed de `roles`) es
TASK-018, ambas de Ivonne. Los endpoints de TASK-019..023 dependen de estas
dos funciones por su firma, asi que TASK-018 puede reemplazar el cuerpo sin
tocar las rutas.

Contrato del token de acceso (documentado en docs/contrato_api.md):
- `sub`: id del usuario (entero, como texto).
- `rol`: nombre del rol (`autoridad`, `sedes`, `epidemiologo`,
  `coordinador_municipal`, `admin`; ver design.md §3).
- `municipio_asignado_id` (opcional): municipio del usuario, si aplica.
- `exp`: expiracion (la valida python-jose).
- `type` (opcional): si existe y es `refresh`, el token se rechaza como
  token de acceso.

`SECRET_KEY` y `ALGORITHM` salen de variables de entorno (NFR-005, regla 6 de
CLAUDE.md); no hay valores por defecto para la clave.
"""

import logging
import os
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

ROL_AUTORIDAD = "autoridad"
ROL_SEDES = "sedes"
ROL_EPIDEMIOLOGO = "epidemiologo"
ROL_COORDINADOR = "coordinador_municipal"
ROL_ADMIN = "admin"

ROLES = frozenset(
    {ROL_AUTORIDAD, ROL_SEDES, ROL_EPIDEMIOLOGO, ROL_COORDINADOR, ROL_ADMIN}
)

# Roles que ven el detalle tecnico de una prediccion (variables explicativas,
# modelo). El resto recibe la vista resumida (REQ-007). Criterio de minimo
# privilegio: ampliar la lista es un cambio de una linea.
ROLES_DETALLE_COMPLETO = frozenset({ROL_EPIDEMIOLOGO, ROL_ADMIN})

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class UsuarioActual:
    id: int
    rol: str
    municipio_asignado_id: int | None = None

    @property
    def ve_detalle_completo(self) -> bool:
        return self.rol in ROLES_DETALLE_COMPLETO


def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _configuracion_jwt() -> tuple[str, str]:
    clave = os.environ.get("SECRET_KEY")
    if not clave:
        # Error de despliegue, no del cliente: no se acepta ningun token.
        logger.error("SECRET_KEY no esta definida; no se pueden validar tokens.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuracion de seguridad incompleta.",
        )
    return clave, os.environ.get("ALGORITHM", "HS256")


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UsuarioActual:
    """Exige un JWT de acceso valido y devuelve el usuario autenticado."""
    if credenciales is None:
        raise _no_autenticado("Se requiere un token de acceso.")
    clave, algoritmo = _configuracion_jwt()
    try:
        # `algorithms` fijo: nunca se acepta el algoritmo declarado por el token.
        payload = jwt.decode(credenciales.credentials, clave, algorithms=[algoritmo])
    except JWTError:
        raise _no_autenticado("Token invalido o expirado.")

    if payload.get("type") == "refresh":
        raise _no_autenticado("Un token de refresco no sirve como token de acceso.")
    rol = payload.get("rol")
    try:
        usuario_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise _no_autenticado("Token sin identificador de usuario valido.")
    if rol not in ROLES:
        raise _no_autenticado("Token con rol desconocido.")

    municipio = payload.get("municipio_asignado_id")
    if municipio is not None and (isinstance(municipio, bool) or not isinstance(municipio, int)):
        raise _no_autenticado("Token con municipio asignado invalido.")
    return UsuarioActual(id=usuario_id, rol=rol, municipio_asignado_id=municipio)


def require_role(*roles: str) -> Callable[..., UsuarioActual]:
    """Dependencia que exige autenticacion y que el rol este en `roles`.

    401 si no hay token valido; 403 si el rol no esta autorizado.
    """
    desconocidos = set(roles) - ROLES
    if desconocidos:
        raise ValueError(f"Roles desconocidos en require_role: {sorted(desconocidos)}")
    permitidos = frozenset(roles)

    def _dependencia(usuario: UsuarioActual = Depends(get_usuario_actual)) -> UsuarioActual:
        if usuario.rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu rol no tiene acceso a este recurso.",
            )
        return usuario

    return _dependencia
