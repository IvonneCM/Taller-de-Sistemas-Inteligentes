"""TASK-012: pruebas del baseline XGBoost, sin base de datos."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.features import generar_features

HAY_XGBOOST = importlib.util.find_spec("xgboost") is not None

if HAY_XGBOOST:
    from app.ml import entrenamiento


def panel_sintetico(
    municipios=("A", "B"),
    semanas=12,
    enfermedad="dengue",
) -> pd.DataFrame:
    filas = []
    for indice, municipio in enumerate(municipios):
        for semana in range(1, semanas + 1):
            filas.append(
                {
                    "municipio": municipio,
                    "enfermedad": enfermedad,
                    "anio": 2026,
                    "semana_epidemiologica": semana,
                    "casos_dengue": float((semana + indice) % 4),
                    "temperatura_media": 20.0 + semana + indice,
                    "humedad_media": 60.0 + semana,
                    "precipitacion_total_mm": 1.0 * semana + indice,
                    "casos_dengue_t_mas_3": (
                        float((semana + indice) % 3 == 0)
                        if semana <= semanas - 3
                        else np.nan
                    ),
                    "casos_dengue_t_mas_4": (
                        float((semana + indice) % 2 == 0)
                        if semana <= semanas - 4
                        else np.nan
                    ),
                }
            )
    return pd.DataFrame(filas)


@unittest.skipUnless(HAY_XGBOOST, "XGBoost no esta instalado.")
class TestEtiquetasYParticiones(unittest.TestCase):
    def setUp(self):
        self.datos = generar_features(panel_sintetico())

    def test_etiqueta_binaria_y_faltantes(self):
        etiqueta = entrenamiento.construir_etiqueta(self.datos, 3)
        objetivo = self.datos.objetivos["casos_dengue_t_mas_3"]
        self.assertTrue(etiqueta.loc[objetivo.isna()].isna().all())
        self.assertTrue(set(etiqueta.dropna().unique()) <= {0.0, 1.0})
        positivos = (objetivo > 0) & objetivo.notna()
        self.assertTrue((etiqueta.loc[positivos] == 1.0).all())

    def test_horizonte_invalido(self):
        with self.assertRaises(ValueError):
            entrenamiento.construir_etiqueta(self.datos, 2)
        with self.assertRaises(ValueError):
            entrenamiento.particiones_walk_forward(self.datos, 5)

    def test_walk_forward_no_mezcla_futuro(self):
        particiones = entrenamiento.particiones_walk_forward(
            self.datos, 3
        )
        self.assertEqual(len(particiones), 3)
        fechas = self.datos.claves["fecha_semana"]
        for particion in particiones:
            disponibles = (
                fechas.loc[particion.train]
                + pd.Timedelta(weeks=4)
            )
            self.assertTrue((disponibles <= particion.origen).all())
            self.assertTrue(
                (fechas.loc[particion.test] == particion.origen).all()
            )
            self.assertFalse(
                set(particion.train).intersection(particion.test)
            )

    def test_walk_forward_t4_tiene_un_origen(self):
        particiones = entrenamiento.particiones_walk_forward(
            self.datos, 4
        )
        self.assertEqual(len(particiones), 1)
        self.assertEqual(
            particiones[0].origen.date().isoformat(), "2026-02-16"
        )

    def test_historia_completa_reduce_train(self):
        flexible = entrenamiento.particiones_walk_forward(
            self.datos, 3, exigir_historia_completa=False
        )
        estricta = entrenamiento.particiones_walk_forward(
            self.datos, 3, exigir_historia_completa=True
        )
        self.assertLess(
            sum(len(p.train) for p in estricta),
            sum(len(p.train) for p in flexible),
        )


@unittest.skipUnless(HAY_XGBOOST, "XGBoost no esta instalado.")
class TestMetricasYBaselines(unittest.TestCase):
    def test_metricas_perfectas(self):
        y = np.array([0, 0, 1, 1])
        proba = np.array([0.0, 0.0, 1.0, 1.0])
        met = entrenamiento.calcular_metricas(y, proba)
        self.assertEqual(met["accuracy"], 1.0)
        self.assertEqual(met["f1"], 1.0)
        self.assertEqual(met["roc_auc"], 1.0)
        self.assertEqual(met["brier"], 0.0)
        self.assertEqual(met["matriz_confusion"], {"tn": 2, "fp": 0, "fn": 0, "tp": 2})

    def test_metricas_una_sola_clase(self):
        met = entrenamiento.calcular_metricas(
            np.zeros(4, dtype=int), np.full(4, 0.1)
        )
        self.assertIsNone(met["roc_auc"])
        self.assertIsNone(met["pr_auc"])
        self.assertEqual(met["positivos"], 0)

    def test_baselines_generan_claves_esperadas(self):
        X = pd.DataFrame(
            {
                "casos_dengue_media_movil_2sem": [0.0, 1.0, 0.0, 2.0],
                "otra": [1, 2, 3, 4],
            }
        )
        y_train = pd.Series([0, 0, 1, 1])
        baselines = entrenamiento.calcular_baselines(
            X, y_train, X, y_train
        )
        self.assertIn("clase_mayoritaria", baselines)
        self.assertIn("casos_recientes", baselines)
        self.assertEqual(
            baselines["casos_recientes"]["positivos"], 2
        )


@unittest.skipUnless(HAY_XGBOOST, "XGBoost no esta instalado.")
class TestEntrenamientoYArtefactos(unittest.TestCase):
    def test_entrenamiento_walk_forward_y_agregados(self):
        datos = generar_features(panel_sintetico())
        detalle, agregado = entrenamiento._entrenar_y_evaluar(datos, 3)
        self.assertEqual(len(detalle), 3)
        self.assertIn("modelo", agregado)
        self.assertIn("clase_mayoritaria", agregado)
        self.assertIn("pooled", agregado["modelo"])
        self.assertIn("macro", agregado["modelo"])
        self.assertGreater(agregado["modelo"]["pooled"]["n"], 0)

    def test_artefacto_roundtrip_y_orden_de_features(self):
        datos = generar_features(panel_sintetico())
        with tempfile.TemporaryDirectory() as temporal:
            metadata = entrenamiento.ejecutar_horizonte(
                datos,
                3,
                guardar=True,
                directorio=Path(temporal),
            )
            artefacto = entrenamiento.cargar_artefacto(
                3, directorio=Path(temporal)
            )
            self.assertEqual(artefacto.features, metadata["features"])
            proba = entrenamiento.predecir_probabilidad(
                artefacto, datos.features.iloc[-1:]
            )
            self.assertEqual(proba.shape, (1,))
            self.assertTrue(0.0 <= float(proba[0]) <= 1.0)

            incompleto = datos.features.iloc[-1:].drop(
                columns=[metadata["features"][0]]
            )
            with self.assertRaises(ValueError):
                entrenamiento.predecir_probabilidad(artefacto, incompleto)

    def test_artefacto_inexistente(self):
        with tempfile.TemporaryDirectory() as temporal:
            with self.assertRaises(FileNotFoundError):
                entrenamiento.cargar_artefacto(
                    3, directorio=Path(temporal)
                )


if __name__ == "__main__":
    unittest.main()
