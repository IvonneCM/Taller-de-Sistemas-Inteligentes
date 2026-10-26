"""TASK-014: pruebas del pipeline de prediccion, sin base de datos real."""

import importlib.util
import math
import os
import unittest
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

# app.models importa app.core.database, que exige DATABASE_URL. Los tests no
# abren conexiones; solo construyen y simulan filas ORM.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5432/test_no_conectar",
)

from app.ml.prediccion import (  # noqa: E402
    PrediccionCalculada,
    calcular_fecha_estimada_riesgo,
    clasificar_nivel_confianza,
    clasificar_nivel_riesgo,
    columnas_climaticas,
    construir_fila_orm,
    estimar_porcentaje_faltante_climatico,
    generar_predicciones,
    persistir_predicciones,
    validar_porcentaje_faltante,
)

HAY_XGBOOST = importlib.util.find_spec("xgboost") is not None
HAY_SHAP = importlib.util.find_spec("shap") is not None


def prediccion_publicada(**cambios) -> PrediccionCalculada:
    datos = dict(
        municipio="guayaramerin",
        enfermedad="dengue",
        horizonte_semanas=3,
        fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
        fecha_estimada_riesgo=date(2026, 4, 20),
        probabilidad_pct=72.5,
        nivel_riesgo="alto",
        nivel_confianza="alto",
        variables_explicativas=(
            {"variable": "casos_dengue_lag2", "peso": 0.4},
        ),
        publicada=True,
        motivo_no_publicacion=None,
    )
    datos.update(cambios)
    return PrediccionCalculada(**datos)


class TestCortesDeRiesgo(unittest.TestCase):
    def test_cortes_provisionales(self):
        self.assertEqual(clasificar_nivel_riesgo(0.0), "bajo")
        self.assertEqual(clasificar_nivel_riesgo(33.32), "bajo")
        self.assertEqual(clasificar_nivel_riesgo(33.33), "medio")
        self.assertEqual(clasificar_nivel_riesgo(66.66), "medio")
        self.assertEqual(clasificar_nivel_riesgo(66.67), "alto")
        self.assertEqual(clasificar_nivel_riesgo(100.0), "alto")

    def test_probabilidad_invalida(self):
        for valor in (-0.01, 100.01, math.nan, math.inf):
            with self.assertRaises(ValueError):
                clasificar_nivel_riesgo(valor)


class TestNivelConfianzaNFR007(unittest.TestCase):
    def test_umbrales_estrictos(self):
        self.assertEqual(clasificar_nivel_confianza(0.0), "alto")
        self.assertEqual(clasificar_nivel_confianza(5.0), "alto")
        self.assertEqual(clasificar_nivel_confianza(5.01), "bajo")
        self.assertEqual(clasificar_nivel_confianza(20.0), "bajo")
        self.assertIsNone(clasificar_nivel_confianza(20.01))
        self.assertIsNone(clasificar_nivel_confianza(100.0))

    def test_porcentaje_invalido(self):
        for valor in (-0.1, 100.1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                validar_porcentaje_faltante(valor)


class TestFechasYFaltantes(unittest.TestCase):
    def test_horizontes_21_y_28_dias(self):
        self.assertEqual(
            calcular_fecha_estimada_riesgo(date(2026, 3, 30), 3),
            date(2026, 4, 20),
        )
        self.assertEqual(
            calcular_fecha_estimada_riesgo(date(2026, 3, 30), 4),
            date(2026, 4, 27),
        )

    def test_horizonte_invalido(self):
        with self.assertRaises(ValueError):
            calcular_fecha_estimada_riesgo(date(2026, 3, 30), 2)
        with self.assertRaises(ValueError):
            calcular_fecha_estimada_riesgo(date(2026, 3, 30), 5)

    def test_fecha_naive_se_asume_utc(self):
        fecha = datetime(2026, 3, 30, 12, 0)
        resultado = calcular_fecha_estimada_riesgo(fecha, 3)
        self.assertEqual(resultado, date(2026, 4, 20))

    def test_estimacion_por_features_climaticas(self):
        fila = pd.Series(
            {
                "casos_dengue_lag2": 1.0,
                "temperatura_media_lag2": 20.0,
                "temperatura_media_lag3": np.nan,
                "humedad_media_lag2": 60.0,
                "precipitacion_total_mm_lag2": 5.0,
            }
        )
        columnas = columnas_climaticas(list(fila.index))
        self.assertEqual(
            columnas,
            [
                "temperatura_media_lag2",
                "temperatura_media_lag3",
                "humedad_media_lag2",
                "precipitacion_total_mm_lag2",
            ],
        )
        self.assertEqual(
            estimar_porcentaje_faltante_climatico(fila, columnas), 25.0
        )


class TestFilaORM(unittest.TestCase):
    def test_construye_fila_valida(self):
        fila = construir_fila_orm(
            prediccion_publicada(),
            municipio_id=1,
            enfermedad_id=1,
            modelo_id=2,
        )
        self.assertEqual(fila.municipio_id, 1)
        self.assertEqual(fila.enfermedad_id, 1)
        self.assertEqual(fila.modelo_id, 2)
        self.assertEqual(fila.nivel_riesgo, "alto")
        self.assertEqual(float(fila.probabilidad_pct), 72.5)
        self.assertEqual(fila.variables_explicativas[0]["variable"], "casos_dengue_lag2")

    def test_rechaza_no_publicada(self):
        with self.assertRaises(ValueError):
            construir_fila_orm(
                prediccion_publicada(publicada=False),
                municipio_id=1,
                enfermedad_id=1,
                modelo_id=2,
            )

    def test_rechaza_sin_explicaciones(self):
        with self.assertRaises(ValueError):
            construir_fila_orm(
                prediccion_publicada(variables_explicativas=()),
                municipio_id=1,
                enfermedad_id=1,
                modelo_id=2,
            )

    def test_rechaza_horizonte_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            construir_fila_orm(
                prediccion_publicada(fecha_estimada_riesgo=date(2026, 4, 19)),
                municipio_id=1,
                enfermedad_id=1,
                modelo_id=2,
            )


class _ModeloFake:
    id = 1


class _MunicipioFake:
    def __init__(self, id_, nombre):
        self.id = id_
        self.nombre = nombre


class _EnfermedadFake:
    def __init__(self, id_, nombre):
        self.id = id_
        self.nombre = nombre


class _QueryFake:
    def __init__(self, filas):
        self._filas = filas

    def all(self):
        return list(self._filas)


class _SessionFake:
    def __init__(self):
        self.agregadas = []
        self.commit_llamado = False
        self.municipios = [_MunicipioFake(10, "GUAYARAMERIN")]
        self.enfermedades = [_EnfermedadFake(20, "dengue")]

    def get(self, _modelo, identificador):
        return _ModeloFake() if identificador == 1 else None

    def query(self, modelo):
        if modelo.__name__ == "Municipio":
            return _QueryFake(self.municipios)
        return _QueryFake(self.enfermedades)

    def add(self, fila):
        fila.id = len(self.agregadas) + 1
        self.agregadas.append(fila)

    def flush(self):
        pass

    def commit(self):
        self.commit_llamado = True

    def close(self):
        pass


class TestPersistenciaSinBD(unittest.TestCase):
    def test_inserta_solo_publicadas_del_catalogo(self):
        session = _SessionFake()
        predicciones = [
            prediccion_publicada(),
            prediccion_publicada(municipio="caranavi"),
            prediccion_publicada(
                publicada=False,
                probabilidad_pct=None,
                nivel_riesgo=None,
                nivel_confianza=None,
                variables_explicativas=(),
                motivo_no_publicacion="datos_insuficientes",
            ),
        ]
        resumen = persistir_predicciones(
            predicciones, modelo_id=1, session=session
        )
        self.assertEqual(resumen["insertadas"], [1])
        self.assertEqual(resumen["no_publicadas"], 1)
        self.assertEqual(len(resumen["omitidas"]), 1)
        self.assertEqual(
            resumen["omitidas"][0]["motivo"], "municipio_no_en_catalogo"
        )
        self.assertFalse(session.commit_llamado)

    def test_rechaza_modelo_inexistente(self):
        with self.assertRaises(ValueError):
            persistir_predicciones(
                [prediccion_publicada()], modelo_id=99, session=_SessionFake()
            )


@unittest.skipUnless(HAY_XGBOOST, "XGBoost no esta instalado.")
class TestPipelineConModeloReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.ml.features import cargar_features

        cls.resultado = cargar_features()

    def _explicador(self, datos, horizonte):
        return [
            {
                "horizonte_semanas": horizonte,
                "explicaciones": [
                    {"variable": columna, "peso": 1.0 / (pos + 1)}
                    for pos, columna in enumerate(datos.columns)
                ],
            }
            for _ in range(len(datos))
        ]

    def test_genera_una_prediccion_por_municipio(self):
        predicciones = generar_predicciones(
            self.resultado,
            horizonte=3,
            fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
            explicador=self._explicador,
        )
        self.assertEqual(len(predicciones), 28)
        self.assertEqual(
            len({p.municipio for p in predicciones}), 28
        )
        for prediccion in predicciones:
            self.assertTrue(prediccion.publicada)
            self.assertEqual(prediccion.fecha_estimada_riesgo, date(2026, 4, 20))
            self.assertIn(prediccion.nivel_riesgo, {"bajo", "medio", "alto"})
            self.assertEqual(prediccion.nivel_confianza, "alto")
            self.assertTrue(0.0 <= prediccion.probabilidad_pct <= 100.0)
            self.assertEqual(len(prediccion.variables_explicativas), 24)

    def test_no_publica_sobre_20_por_ciento(self):
        llamado = {"veces": 0}

        def explicador(datos, horizonte):
            llamado["veces"] += 1
            return self._explicador(datos, horizonte)

        predicciones = generar_predicciones(
            self.resultado,
            horizonte=3,
            fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
            porcentajes_faltantes=20.01,
            explicador=explicador,
        )
        self.assertEqual(llamado["veces"], 0)
        for prediccion in predicciones:
            self.assertFalse(prediccion.publicada)
            self.assertIsNone(prediccion.nivel_confianza)
            self.assertEqual(
                prediccion.motivo_no_publicacion, "datos_insuficientes"
            )
            self.assertEqual(prediccion.variables_explicativas, ())

    def test_confianza_baja_entre_5_y_20(self):
        predicciones = generar_predicciones(
            self.resultado,
            horizonte=3,
            fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
            porcentajes_faltantes=10.0,
            explicador=self._explicador,
        )
        self.assertTrue(all(p.publicada for p in predicciones))
        self.assertTrue(all(p.nivel_confianza == "bajo" for p in predicciones))

    @unittest.skipUnless(HAY_SHAP, "SHAP no esta instalado.")
    def test_pipeline_real_con_shap(self):
        predicciones = generar_predicciones(
            self.resultado,
            horizonte=3,
            fecha_generacion=datetime(2026, 3, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(len(predicciones), 28)
        for prediccion in predicciones:
            self.assertTrue(prediccion.publicada)
            self.assertEqual(len(prediccion.variables_explicativas), 24)
            self.assertTrue(
                all(
                    math.isfinite(item["peso"])
                    for item in prediccion.variables_explicativas
                )
            )


if __name__ == "__main__":
    unittest.main()
