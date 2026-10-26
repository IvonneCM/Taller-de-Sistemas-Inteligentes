"""Restricciones de BD de `predicciones`, `alertas`, `umbrales_configuracion`
y `brotes_confirmados` (design.md §3; REQ-001/002/003/005/010)."""

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Alerta, BroteConfirmado, Prediccion, UmbralConfiguracion
from tests.api.helpers import crear_modelo, crear_prediccion


@pytest.fixture()
def contexto(db_session, catalogo):
    dengue = catalogo["enfermedades"]["dengue"]
    return {
        "municipio": catalogo["municipios"]["GUAYARAMERIN"],
        "enfermedad": dengue,
        "modelo": crear_modelo(db_session, dengue),
        "departamento": catalogo["departamentos"]["Beni"],
    }


def _insertar_debe_fallar(db, objeto, restriccion):
    with pytest.raises(IntegrityError) as error:
        with db.begin_nested():
            db.add(objeto)
            db.flush()
    assert restriccion in str(error.value)


def _prediccion(contexto, **cambios):
    generada = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
    datos = dict(
        municipio_id=contexto["municipio"].id,
        enfermedad_id=contexto["enfermedad"].id,
        modelo_id=contexto["modelo"].id,
        fecha_generacion=generada,
        fecha_estimada_riesgo=date(2026, 3, 2) + timedelta(days=25),
        nivel_riesgo="alto",
        probabilidad_pct=80,
        nivel_confianza="medio",
        variables_explicativas=[{"variable": "x", "peso": 0.1}],
    )
    datos.update(cambios)
    return Prediccion(**datos)


@pytest.mark.parametrize("dias", [21, 25, 28])
def test_prediccion_acepta_horizonte_de_21_a_28_dias(db_session, contexto, dias):
    prediccion = _prediccion(
        contexto, fecha_estimada_riesgo=date(2026, 3, 2) + timedelta(days=dias)
    )
    db_session.add(prediccion)
    db_session.flush()
    assert prediccion.id is not None


@pytest.mark.parametrize("dias", [0, 20, 29, 60])
def test_prediccion_rechaza_horizonte_fuera_de_21_a_28_dias(db_session, contexto, dias):
    _insertar_debe_fallar(
        db_session,
        _prediccion(contexto, fecha_estimada_riesgo=date(2026, 3, 2) + timedelta(days=dias)),
        "ck_prediccion_horizonte_21_28_dias",
    )


def test_horizonte_se_mide_con_la_fecha_utc(db_session, contexto):
    # 23:30 en La Paz (UTC-4) del 1 de marzo ya es 2 de marzo en UTC: la
    # ventana se cuenta desde la fecha UTC, sin depender de la zona de sesion.
    generada = datetime(2026, 3, 2, 3, 30, tzinfo=timezone.utc)
    ok = _prediccion(
        contexto, fecha_generacion=generada,
        fecha_estimada_riesgo=date(2026, 3, 2) + timedelta(days=21),
    )
    db_session.add(ok)
    db_session.flush()
    _insertar_debe_fallar(
        db_session,
        _prediccion(
            contexto, fecha_generacion=generada,
            fecha_estimada_riesgo=date(2026, 3, 2) + timedelta(days=20),
        ),
        "ck_prediccion_horizonte_21_28_dias",
    )


def test_prediccion_rechaza_nivel_de_riesgo_invalido(db_session, contexto):
    _insertar_debe_fallar(
        db_session, _prediccion(contexto, nivel_riesgo="critico"),
        "ck_prediccion_nivel_riesgo",
    )


def test_prediccion_rechaza_confianza_invalida(db_session, contexto):
    _insertar_debe_fallar(
        db_session, _prediccion(contexto, nivel_confianza="altisimo"),
        "ck_prediccion_nivel_confianza",
    )


@pytest.mark.parametrize("probabilidad", [-0.01, 100.01, 150])
def test_prediccion_rechaza_probabilidad_fuera_de_rango(db_session, contexto, probabilidad):
    _insertar_debe_fallar(
        db_session, _prediccion(contexto, probabilidad_pct=probabilidad),
        "ck_prediccion_probabilidad_0_100",
    )


@pytest.mark.parametrize("probabilidad", [0, 70.5, 100])
def test_prediccion_acepta_probabilidad_en_rango(db_session, contexto, probabilidad):
    db_session.add(_prediccion(contexto, probabilidad_pct=probabilidad))
    db_session.flush()


def test_prediccion_exige_variables_explicativas_no_nulas(db_session, contexto):
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(_prediccion(contexto, variables_explicativas=None))
            db_session.flush()


@pytest.mark.parametrize("valor", [{"variable": "x"}, "texto", 3])
def test_prediccion_exige_que_las_variables_explicativas_sean_una_lista(
    db_session, contexto, valor
):
    _insertar_debe_fallar(
        db_session, _prediccion(contexto, variables_explicativas=valor),
        "ck_prediccion_variables_es_lista",
    )


def test_alerta_rechaza_justificacion_vacia_o_en_blanco(db_session, contexto):
    prediccion = crear_prediccion(
        db_session, municipio=contexto["municipio"],
        enfermedad=contexto["enfermedad"], modelo=contexto["modelo"],
    )
    for texto in ("", "   "):
        _insertar_debe_fallar(
            db_session,
            Alerta(prediccion_id=prediccion.id, umbral_aplicado=70, justificacion=texto),
            "ck_alerta_justificacion_no_vacia",
        )


def test_alerta_exige_justificacion_no_nula(db_session, contexto):
    prediccion = crear_prediccion(
        db_session, municipio=contexto["municipio"],
        enfermedad=contexto["enfermedad"], modelo=contexto["modelo"],
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(Alerta(prediccion_id=prediccion.id, umbral_aplicado=70))
            db_session.flush()


def test_alerta_rechaza_umbral_fuera_de_rango(db_session, contexto):
    prediccion = crear_prediccion(
        db_session, municipio=contexto["municipio"],
        enfermedad=contexto["enfermedad"], modelo=contexto["modelo"],
    )
    _insertar_debe_fallar(
        db_session,
        Alerta(prediccion_id=prediccion.id, umbral_aplicado=101, justificacion="x"),
        "ck_alerta_umbral_0_100",
    )


def test_umbral_rechaza_valores_fuera_de_0_100(db_session, contexto):
    for valor in (-1, 100.5):
        _insertar_debe_fallar(
            db_session,
            UmbralConfiguracion(
                enfermedad_id=contexto["enfermedad"].id, umbral_probabilidad_pct=valor
            ),
            "ck_umbral_0_100",
        )


def test_umbral_unico_por_enfermedad_y_departamento_incluso_con_departamento_nulo(
    db_session, contexto
):
    enfermedad, departamento = contexto["enfermedad"], contexto["departamento"]
    db_session.add_all(
        [
            UmbralConfiguracion(enfermedad_id=enfermedad.id, umbral_probabilidad_pct=60),
            UmbralConfiguracion(
                enfermedad_id=enfermedad.id, departamento_id=departamento.id,
                umbral_probabilidad_pct=50,
            ),
        ]
    )
    db_session.flush()
    # NULLS NOT DISTINCT: dos umbrales "generales" tampoco se permiten.
    _insertar_debe_fallar(
        db_session,
        UmbralConfiguracion(enfermedad_id=enfermedad.id, umbral_probabilidad_pct=65),
        "uq_umbral_enfermedad_departamento",
    )
    _insertar_debe_fallar(
        db_session,
        UmbralConfiguracion(
            enfermedad_id=enfermedad.id, departamento_id=departamento.id,
            umbral_probabilidad_pct=55,
        ),
        "uq_umbral_enfermedad_departamento",
    )


def test_brote_confirmado_exige_zona_enfermedad_fecha_y_fuente(db_session, contexto):
    ok = BroteConfirmado(
        municipio_id=contexto["municipio"].id,
        enfermedad_id=contexto["enfermedad"].id,
        fecha_confirmacion=date(2026, 3, 30),
        fuente="boletin de ejemplo",
    )
    db_session.add(ok)
    db_session.flush()
    for faltante in ("municipio_id", "enfermedad_id", "fecha_confirmacion", "fuente"):
        datos = dict(
            municipio_id=contexto["municipio"].id,
            enfermedad_id=contexto["enfermedad"].id,
            fecha_confirmacion=date(2026, 3, 30),
            fuente="x",
        )
        datos[faltante] = None
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.add(BroteConfirmado(**datos))
                db_session.flush()
