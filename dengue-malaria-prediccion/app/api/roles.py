"""Nombres de rol (design.md §3) y permisos por vista, compartidos por las
rutas de TASK-019 a 023. La autenticacion y `require_role` viven en deps.py
(TASK-017/018)."""

ROL_AUTORIDAD = "autoridad"
ROL_SEDES = "sedes"
ROL_EPIDEMIOLOGO = "epidemiologo"
ROL_COORDINADOR = "coordinador_municipal"
ROL_ADMIN = "admin"

ROLES = frozenset(
    {ROL_AUTORIDAD, ROL_SEDES, ROL_EPIDEMIOLOGO, ROL_COORDINADOR, ROL_ADMIN}
)

# Roles que ven el detalle tecnico de una prediccion (variables explicativas y
# modelo); el resto recibe la vista resumida (REQ-007). Minimo privilegio:
# ampliar la lista es un cambio de una linea.
ROLES_DETALLE_COMPLETO = frozenset({ROL_EPIDEMIOLOGO, ROL_ADMIN})
