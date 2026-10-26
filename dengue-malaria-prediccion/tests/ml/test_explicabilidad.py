"""TASK-013: contrato aislado e integración sin entrenar ni escribir artefactos."""

import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from app.ml import explicabilidad as modulo


class TestContrato(unittest.TestCase):
    def setUp(self):
        self.columnas = [f"variable_{i}" for i in range(24)]
        self.X = pd.DataFrame(np.ones((2, 24)), columns=self.columnas)
        self.artefacto = SimpleNamespace(features=self.columnas)
        self.carga = patch.object(modulo, "_cargar_artefacto", return_value=self.artefacto)
        self.mock_carga = self.carga.start()
        self.addCleanup(self.carga.stop)
        pesos = np.zeros((2, 24))
        pesos[:, :2] = [-0.75, 0.25]
        self.calculo = patch.object(
            modulo, "_calcular_shap", return_value=(pesos, 0.2, np.array([-0.3, -0.3]))
        )
        self.mock_calculo = self.calculo.start()
        self.addCleanup(self.calculo.stop)

    def test_contrato_ranking_signo_y_aditividad_ambos_horizontes(self):
        for horizonte in (3, 4):
            with self.subTest(horizonte=horizonte):
                self.mock_calculo.return_value = (np.pad([[-0.75, 0.25]], ((0, 0), (0, 22))), 0.2, np.array([-0.3]))
                respuesta = modulo.explicar_observacion(self.X.iloc[:1], horizonte)
                self.assertEqual(respuesta["horizonte_semanas"], horizonte)
                self.assertEqual(respuesta["escala"], "log_odds")
                self.assertEqual(len(respuesta["explicaciones"]), 24)
                self.assertEqual(respuesta["explicaciones"][0], {"variable": "variable_0", "peso": -0.75})
                self.assertEqual(respuesta["explicaciones"][1]["peso"], 0.25)
                self.assertAlmostEqual(respuesta["valor_base"] + sum(p["peso"] for p in respuesta["explicaciones"]), respuesta["salida_modelo"])
                json.dumps(respuesta, allow_nan=False)
                self.mock_carga.assert_called_with(horizonte, None)

    def test_lote_conserva_orden_y_nan_sin_mutar(self):
        self.X.iloc[0, 0] = np.nan
        original = self.X.copy(deep=True)
        respuesta = modulo.explicar_observaciones(self.X, 3)
        self.assertEqual(len(respuesta), 2)
        entrada = self.mock_calculo.call_args.args[1]
        self.assertTrue(np.isnan(entrada.iloc[0, 0]))
        self.assertEqual(entrada.iloc[1, 0], 1.0)
        pd.testing.assert_frame_equal(original, self.X)

    def test_horizontes_invalidos(self):
        for valor in (2, 5, True, 3.0, "3", None):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                modulo.explicar_observaciones(self.X, valor)
        self.mock_carga.assert_not_called()

    def test_artefacto_inexistente_no_fabrica_explicacion(self):
        self.mock_carga.side_effect = FileNotFoundError("artefacto ausente")
        with self.assertRaises(FileNotFoundError):
            modulo.explicar_observaciones(self.X, 4, directorio=Path("ausente"))
        self.mock_calculo.assert_not_called()

    def test_error_de_carga_se_propaga(self):
        self.mock_carga.side_effect = ValueError("JSON inválido")
        with self.assertRaisesRegex(ValueError, "JSON inválido"):
            modulo.explicar_observaciones(self.X, 3)
        self.mock_calculo.assert_not_called()

    def test_esquema_incorrecto(self):
        entradas = [self.X.drop(columns=self.columnas[0]), self.X.assign(extra=1), self.X[self.columnas[::-1]], pd.concat([self.X, self.X.iloc[:, :1]], axis=1)]
        for entrada in entradas:
            with self.subTest(columnas=list(entrada.columns)), self.assertRaises(ValueError):
                modulo.explicar_observaciones(entrada, 3)
        self.mock_calculo.assert_not_called()

    def test_datos_incompatibles(self):
        for valor in ("texto", "1", True, 1j, np.inf, -np.inf, 1e100):
            entrada = self.X.copy().astype(object)
            entrada[self.columnas[0]] = valor
            with self.subTest(valor=valor), self.assertRaises((ValueError, TypeError)):
                modulo.explicar_observaciones(entrada, 3)
        self.mock_calculo.assert_not_called()

    def test_nullable_conserva_faltantes(self):
        entrada = self.X.astype("Float64")
        entrada.iloc[0, 0] = pd.NA
        modulo.explicar_observaciones(entrada, 4)
        self.assertTrue(np.isnan(self.mock_calculo.call_args.args[1].iloc[0, 0]))

    def test_tipo_y_numero_de_filas(self):
        with self.assertRaises(TypeError):
            modulo.explicar_observaciones(self.X.to_numpy(), 3)
        with self.assertRaises(ValueError):
            modulo.explicar_observaciones(self.X.iloc[:0], 3)
        for entrada in (self.X, self.X.iloc[:0]):
            with self.assertRaises(ValueError):
                modulo.explicar_observacion(entrada, 3)

    def test_fallo_de_aditividad(self):
        self.mock_calculo.return_value = (np.zeros((2, 24)), 0.2, np.ones(2))
        with self.assertRaisesRegex(RuntimeError, "aditiva"):
            modulo.explicar_observaciones(self.X, 3)

    def test_salida_invalida_o_no_finita(self):
        for salida in ((np.zeros((2, 23)), 0, np.zeros(2)), (np.zeros((2, 24)), [0, 1], np.zeros(2)), (np.zeros((2, 24)), np.nan, np.zeros(2)), (np.full((2, 24), np.inf), 0, np.zeros(2)), (np.zeros((2, 24)), 0, np.array([np.nan, 0]))):
            with self.subTest(salida=str(salida)), self.assertRaises(RuntimeError):
                self.mock_calculo.return_value = salida
                modulo.explicar_observaciones(self.X, 3)

    def test_error_shap_no_genera_sustituto(self):
        self.mock_calculo.side_effect = RuntimeError("fallo SHAP")
        with self.assertRaisesRegex(RuntimeError, "fallo SHAP"):
            modulo.explicar_observaciones(self.X, 3)


FALTANTES = [p for p in ("shap", "xgboost", "sklearn") if importlib.util.find_spec(p) is None]


class TestAdaptadorSHAP(unittest.TestCase):
    def test_tree_explainer_y_prediccion_en_la_misma_escala(self):
        modelo = Mock()
        modelo.save_config.return_value = json.dumps({
            "learner": {"objective": {"name": "binary:logistic"}}
        })
        modelo.predict.return_value = np.array([0.3])
        artefacto = SimpleNamespace(modelo=modelo, features=["a", "b"])
        X = pd.DataFrame({"a": [np.nan], "b": [2.0]})
        explicador = Mock(expected_value=0.2)
        explicador.shap_values.return_value = np.array([[-0.1, 0.2]])
        shap = SimpleNamespace(TreeExplainer=Mock(return_value=explicador))
        xgboost = SimpleNamespace(DMatrix=Mock(return_value="matriz"))
        with patch.dict("sys.modules", {"shap": shap, "xgboost": xgboost}):
            pesos, base, margen = modulo._calcular_shap(artefacto, X)
        shap.TreeExplainer.assert_called_once_with(
            modelo, model_output="raw", feature_perturbation="tree_path_dependent"
        )
        explicador.shap_values.assert_called_once_with(X, check_additivity=True)
        self.assertIs(xgboost.DMatrix.call_args.args[0], X)
        self.assertEqual(xgboost.DMatrix.call_args.kwargs["feature_names"], ["a", "b"])
        self.assertTrue(np.isnan(xgboost.DMatrix.call_args.kwargs["missing"]))
        modelo.predict.assert_called_once_with("matriz", output_margin=True)
        np.testing.assert_allclose(base + pesos.sum(axis=1), margen)

    def test_objetivo_incompatible_no_se_etiqueta_log_odds(self):
        modelo = Mock()
        modelo.save_config.return_value = json.dumps({
            "learner": {"objective": {"name": "reg:squarederror"}}
        })
        shap = SimpleNamespace(TreeExplainer=Mock())
        with patch.dict("sys.modules", {"shap": shap, "xgboost": Mock()}):
            with self.assertRaisesRegex(ValueError, "binary:logistic"):
                modulo._calcular_shap(SimpleNamespace(modelo=modelo), pd.DataFrame())
        shap.TreeExplainer.assert_not_called()


@unittest.skipIf(bool(FALTANTES), "Dependencias ausentes: " + ", ".join(FALTANTES))
class TestIntegracionReal(unittest.TestCase):
    def comprobar_horizonte(self, horizonte):
        # Dependencias presentes pero rotas o artefactos ausentes deben fallar.
        from app.ml.entrenamiento import cargar_artefacto, predecir_probabilidad
        from app.ml.features import cargar_features

        artefacto = cargar_artefacto(horizonte)
        resultado = cargar_features()
        X = resultado.features
        self.assertEqual(list(X.columns), artefacto.features)
        # Incluye historia parcial con NaN, completa y totalmente ausente.
        parcial = X.notna().any(axis=1) & X.isna().any(axis=1)
        completa = X.notna().all(axis=1)
        ausente = X.isna().all(axis=1)
        entradas = pd.concat([X.loc[parcial].iloc[:1], X.loc[completa].iloc[:1], X.loc[ausente].iloc[:1]])
        self.assertEqual(len(entradas), 3)
        respuestas = modulo.explicar_observaciones(entradas, horizonte)
        probabilidades = predecir_probabilidad(artefacto, entradas)
        for respuesta, probabilidad in zip(respuestas, probabilidades):
            self.assertEqual(respuesta["horizonte_semanas"], horizonte)
            self.assertEqual(respuesta["escala"], "log_odds")
            ranking = respuesta["explicaciones"]
            self.assertEqual(len(ranking), 24)
            self.assertEqual({p["variable"] for p in ranking}, set(artefacto.features))
            magnitudes = [abs(p["peso"]) for p in ranking]
            self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))
            self.assertAlmostEqual(respuesta["valor_base"] + sum(p["peso"] for p in ranking), respuesta["salida_modelo"], places=4)
            self.assertAlmostEqual(1 / (1 + np.exp(-respuesta["salida_modelo"])), float(probabilidad), places=6)
            json.dumps(respuesta, allow_nan=False)
        individual = modulo.explicar_observacion(entradas.iloc[:1], horizonte)
        self.assertEqual(individual, respuestas[0])

    def test_modelo_real_t3(self):
        self.comprobar_horizonte(3)

    def test_modelo_real_t4(self):
        self.comprobar_horizonte(4)


if __name__ == "__main__":
    unittest.main()
