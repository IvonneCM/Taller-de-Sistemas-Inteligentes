"""Utilidades de las pruebas de API: tokens JWT firmados como los emitira
/auth/login (TASK-017) y fabricas de datos de ejemplo.

Los datos son EJEMPLOS de prueba (no cifras epidemiologicas reales): los
nombres de variables y los pesos solo ilustran el formato de REQ-004."""

import os
from datetime import date, datetime, timedelta, timezone

from jose import jwt

from app.models import Alerta, BroteConfirmado, Modelo, Prediccion

VARIABLES_EJEMPLO = [
    {"variable": "casos_media_movil_4s", "peso": 0.42},
    {"variable": "temperatura_media_lag_3", "peso": 0.21},
    {"variable": "precipitacion_acum_lag_2", "peso": -0.08},
]


def crear_token(rol="epidemiologo", usuario_id=1, *, expira_en=timedelta(minutes=30), **extra):
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "exp": datetime.now(timezone.utc) + expira_en,
        **extra,
    }
    return jwt.encode(
        payload, os.environ["SECRET_KEY"], algorithm=os.environ.get("ALGORITHM", "HS256")
    )


def cabeceras(rol="epidemiologo", **kwargs):
    return {"Authorization": f"Bearer {crear_token(rol, **kwargs)}"}


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
