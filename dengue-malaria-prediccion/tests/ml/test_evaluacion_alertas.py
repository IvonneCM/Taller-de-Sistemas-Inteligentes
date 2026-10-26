"""Pruebas unitarias de TASK-015: Evaluacion de alertas (app/ml/evaluacion_alertas.py).

Verifica exhaustivamente:
- REQ-005: Prohibido generar alertas de riesgo sin justificacion explicita (variables del modelo).
- REQ-009: Emision de alerta al superar umbral configurable.
- REQ-010: Lectura dinamica de umbrales (departamento vs general de enfermedad).
- Idempotencia y prevencion de alertas duplicadas.
- Evaluacion por lote y pendientes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.ml.evaluacion_alertas import (
    construir_justificacion,
    evaluar_alertas_lote,
    evaluar_alertas_pendientes,
    evaluar_prediccion,
)
from app.models import Alerta
from app.services.umbrales import configurar_umbral
from tests.api.helpers import crear_modelo, crear_prediccion

BASE_TIME = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
VARS_TEST = [
    {"variable": "temperatura_promedio_lag3", "peso": 0.45},
    {"variable": "casos_dengue_lag2", "peso": 0.32},
]


# ==============================================================================
# Pruebas de construccion de justificacion (sin base de datos)
# ==============================================================================

class TestConstruirJustificacion:
    def test_justificacion_valida_con_variables_y_pesos(self):
        texto = construir_justificacion(
            VARS_TEST, probabilidad_pct=82.5, umbral=70.0
        )
        assert "82.5%" in texto
        assert "70.0%" in texto
        assert "temperatura_promedio_lag3 (peso: 0.45)" in texto
        assert "casos_dengue_lag2 (peso: 0.32)" in texto
        assert len(texto.strip()) > 0

    def test_justificacion_sin_probabilidad_ni_umbral(self):
        texto = construir_justificacion(VARS_TEST)
        assert "Factores explicativos determinantes" in texto
        assert "temperatura_promedio_lag3" in texto

    def test_req005_rechaza_lista_vacia(self):
        with pytest.raises(ValueError, match="REQ-005"):
            construir_justificacion([])

    def test_req005_rechaza_elementos_sin_nombre_de_variable(self):
        with pytest.raises(ValueError, match="REQ-005"):
            construir_justificacion([{"variable": "", "peso": 0.5}])


# ==============================================================================
# Pruebas con base de datos (transaccionales con rollback automatico)
# ==============================================================================

class TestEvaluacionAlertas:
    def test_req005_probabilidad_alta_sin_variables_no_genera_alerta(
        self, db_session, catalogo, caplog
    ):
        """Criterio de aceptacion critico REQ-005 / Verificacion TASK-015:

        Prediccion con probabilidad alta (ej. 85%) pero sin variables
        explicativas (lista vacia) NO genera alerta y se registra en log.
        """
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        # Prediccion con probabilidad alta pero sin explicabilidad
        prediccion = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=85.0,
            variables=[],  # Lista vacia
            generada=BASE_TIME,
        )

        with caplog.at_level(logging.WARNING):
            alerta = evaluar_prediccion(db_session, prediccion)

        # Confirmar que NO se genero alerta
        assert alerta is None
        # Confirmar que no hay filas en la tabla alertas para esta prediccion
        filas = db_session.scalars(
            select(Alerta).where(Alerta.prediccion_id == prediccion.id)
        ).all()
        assert len(filas) == 0

        # Confirmar registro explicito en el log
        assert "REQ-005" in caplog.text
        assert str(prediccion.id) in caplog.text

    def test_req009_supera_umbral_con_variables_genera_alerta(
        self, db_session, catalogo
    ):
        """REQ-009: probabilidad >= umbral con variables explicativas genera alerta."""
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        prediccion = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=78.5,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        alerta = evaluar_prediccion(db_session, prediccion)

        assert alerta is not None
        assert alerta.prediccion_id == prediccion.id
        # Umbral por defecto es 70.00%
        assert alerta.umbral_aplicado == Decimal("70.00")
        assert "temperatura_promedio_lag3" in alerta.justificacion
        assert len(alerta.justificacion.strip()) > 0

        # Verificar persistencia en base de datos
        db_alerta = db_session.scalar(
            select(Alerta).where(Alerta.prediccion_id == prediccion.id)
        )
        assert db_alerta is not None
        assert db_alerta.id == alerta.id

    def test_no_supera_umbral_no_genera_alerta(self, db_session, catalogo):
        """Probabilidad < umbral no debe generar alerta."""
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        # 60% < 70% por defecto
        prediccion = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=60.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        alerta = evaluar_prediccion(db_session, prediccion)
        assert alerta is None

        filas = db_session.scalars(
            select(Alerta).where(Alerta.prediccion_id == prediccion.id)
        ).all()
        assert len(filas) == 0

    def test_req010_cambio_dinamico_de_umbral(self, db_session, catalogo):
        """REQ-010: un cambio de umbral con POST /admin/umbrales se refleja

        en la siguiente evaluacion sin reiniciar la aplicacion ni el servidor.
        """
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        prediccion = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=65.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        # Inicialmente con 70% no genera alerta
        alerta_inicial = evaluar_prediccion(db_session, prediccion)
        assert alerta_inicial is None

        # Admin cambia umbral de dengue a 60%
        configurar_umbral(
            db_session,
            enfermedad_id=dengue.id,
            departamento_id=None,
            umbral_probabilidad_pct=60.0,
        )

        # En la siguiente evaluacion, 65% >= 60% -> SÍ genera alerta
        alerta_posterior = evaluar_prediccion(db_session, prediccion)
        assert alerta_posterior is not None
        assert alerta_posterior.umbral_aplicado == Decimal("60.00")

    def test_umbral_especifico_por_departamento_tiene_prioridad(
        self, db_session, catalogo
    ):
        """Un umbral departamental tiene prioridad sobre el umbral general."""
        dengue = catalogo["enfermedades"]["dengue"]
        beni = catalogo["departamentos"]["Beni"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]  # Beni
        ixiamas = catalogo["municipios"]["IXIAMAS"]  # La Paz
        modelo = crear_modelo(db_session, dengue)

        # Configurar umbral general en 80%, pero para Beni en 55%
        configurar_umbral(
            db_session,
            enfermedad_id=dengue.id,
            departamento_id=None,
            umbral_probabilidad_pct=80.0,
        )
        configurar_umbral(
            db_session,
            enfermedad_id=dengue.id,
            departamento_id=beni.id,
            umbral_probabilidad_pct=55.0,
        )

        # Prediccion de 70% en Guayaramerin (Beni): supera 55% -> ALERTA
        pred_beni = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=70.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )
        alerta_beni = evaluar_prediccion(db_session, pred_beni)
        assert alerta_beni is not None
        assert alerta_beni.umbral_aplicado == Decimal("55.00")

        # Prediccion de 70% en Ixiamas (La Paz): no supera 80% -> SIN ALERTA
        pred_lp = crear_prediccion(
            db_session,
            municipio=ixiamas,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=70.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )
        alerta_lp = evaluar_prediccion(db_session, pred_lp)
        assert alerta_lp is None

    def test_idempotencia_no_duplica_alerta(self, db_session, catalogo):
        """Evaluar dos veces no duplica filas en la tabla alertas."""
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        prediccion = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=90.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        alerta1 = evaluar_prediccion(db_session, prediccion)
        alerta2 = evaluar_prediccion(db_session, prediccion)

        assert alerta1.id == alerta2.id
        total = db_session.scalars(
            select(Alerta).where(Alerta.prediccion_id == prediccion.id)
        ).all()
        assert len(total) == 1

    def test_evaluar_alertas_lote(self, db_session, catalogo):
        """Procesa una lista mixta de predicciones y reporta metricas correctas."""
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        ixiamas = catalogo["municipios"]["IXIAMAS"]
        modelo = crear_modelo(db_session, dengue)

        # 1. Supera umbral con explicacion -> Alerta
        p1 = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=85.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )
        # 2. Supera umbral SIN explicacion -> Omitida por REQ-005
        p2 = crear_prediccion(
            db_session,
            municipio=ixiamas,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=92.0,
            variables=[],
            generada=BASE_TIME,
        )
        # 3. No supera umbral -> No alerta
        p3 = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=45.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        resumen = evaluar_alertas_lote(
            db_session, [p1, p2, p3], commit=False
        )

        assert resumen["total_creadas"] == 1
        assert p1.id in [a for a in db_session.scalars(select(Alerta.prediccion_id)).all()]
        assert p2.id in resumen["omitidas_sin_explicacion"]
        assert resumen["no_superan_umbral"] == 1

    def test_evaluar_alertas_pendientes(self, db_session, catalogo):
        """Busca predicciones que no tengan alerta y las procesa."""
        dengue = catalogo["enfermedades"]["dengue"]
        guayaramerin = catalogo["municipios"]["GUAYARAMERIN"]
        modelo = crear_modelo(db_session, dengue)

        p = crear_prediccion(
            db_session,
            municipio=guayaramerin,
            enfermedad=dengue,
            modelo=modelo,
            probabilidad=88.0,
            variables=VARS_TEST,
            generada=BASE_TIME,
        )

        resumen = evaluar_alertas_pendientes(db_session, limite=10)
        assert resumen["total_creadas"] >= 1
