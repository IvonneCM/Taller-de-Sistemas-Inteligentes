"""Utilidades de las pruebas de API: fabricas de usuarios con token de acceso
(TASK-017) y de datos de ejemplo.

Los datos son EJEMPLOS de prueba (no cifras epidemiologicas reales): los
nombres de variables y los pesos solo ilustran el formato de REQ-004."""

from datetime import date, datetime, timedelta, timezone
from itertools import count

from sqlalchemy import select

from app.core.security import crear_access_token, hash_password
from app.models import Alerta, BroteConfirmado, Modelo, Prediccion, Rol, Usuario

VARIABLES_EJEMPLO = [
    {"variable": "casos_media_movil_4s", "peso": 0.42},
    {"variable": "temperatura_media_lag_3", "peso": 0.21},
    {"variable": "precipitacion_acum_lag_2", "peso": -0.08},
]

# Sesion de BD de la prueba en curso; la fija el fixture autouse de
# tests/api/conftest.py para que `cabeceras()` pueda crear usuarios sin pedir
# la sesion en cada prueba.
_SESION = None
_contador = count(1)


def crear_usuario_con_rol(db, rol_nombre):
    rol = db.execute(select(Rol).where(Rol.nombre == rol_nombre)).scalar_one_or_none()
    if rol is None:
        rol = Rol(nombre=rol_nombre)
        db.add(rol)
        db.flush()
    usuario = Usuario(
        email=f"{rol_nombre}.{next(_contador)}@prueba.local",
        password_hash=hash_password("ClaveSegura123!"),
        rol_id=rol.id,
    )
    db.add(usuario)
    db.flush()
    return usuario


def cabeceras(rol="epidemiologo"):
    """Cabecera Authorization con un access token real de un usuario nuevo
    con ese rol (el rol se lee de la BD, como en produccion)."""
    usuario = crear_usuario_con_rol(_SESION, rol)
    return {"Authorization": f"Bearer {crear_access_token(usuario.id, rol)}"}


def crear_modelo(db, enfermedad, version="v1"):
    modelo = Modelo(
        nombre="baseline_ejemplo",
        version=version,
        enfermedad_id=enfermedad.id,
        fecha_entrenamiento=datetime.now(timezone.utc),
        metricas_entrenamiento={"nota": "ejemplo de prueba"},
    )
    db.add(modelo)
    db.flush()
    return modelo


def crear_prediccion(
    db,
    *,
    municipio,
    enfermedad,
    modelo,
    nivel="alto",
    probabilidad=80,
    confianza="medio",
    generada=None,
    dias=25,
    variables=None,
):
    generada = generada or datetime.now(timezone.utc)
    prediccion = Prediccion(
        municipio_id=municipio.id,
        enfermedad_id=enfermedad.id,
        modelo_id=modelo.id,
        fecha_generacion=generada,
        fecha_estimada_riesgo=generada.astimezone(timezone.utc).date() + timedelta(days=dias),
        nivel_riesgo=nivel,
        probabilidad_pct=probabilidad,
        nivel_confianza=confianza,
        variables_explicativas=VARIABLES_EJEMPLO if variables is None else variables,
    )
    db.add(prediccion)
    db.flush()
    return prediccion


def crear_alerta(db, prediccion, *, umbral=70, justificacion="Probabilidad sobre el umbral.", emitida=None):
    alerta = Alerta(
        prediccion_id=prediccion.id,
        umbral_aplicado=umbral,
        justificacion=justificacion,
        **({"fecha_emision": emitida} if emitida else {}),
    )
    db.add(alerta)
    db.flush()
    return alerta


def crear_brote(db, *, municipio, enfermedad, fecha: date, fuente="boletin de ejemplo"):
    brote = BroteConfirmado(
        municipio_id=municipio.id,
        enfermedad_id=enfermedad.id,
        fecha_confirmacion=fecha,
        fuente=fuente,
    )
    db.add(brote)
    db.flush()
    return brote
