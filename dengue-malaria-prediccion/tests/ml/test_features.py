"""TASK-011: pruebas aisladas, sin BD; ejecutables con unittest o pytest."""

import hashlib
import importlib.util
import io
import math
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta

import pandas as pd
from pandas.testing import assert_frame_equal

from app.ml.features import DATASET_DENGUE, cargar_features, generar_features


def ejemplo(municipio="A", enfermedad="dengue", base=0):
    return pd.DataFrame({
        "municipio": [municipio] * 8,
        "enfermedad": [enfermedad] * 8,
        "anio": [2026] * 8,
        "semana_epidemiologica": range(1, 9),
        "casos_confirmados": [base + i * 10 for i in range(1, 9)],
        "temperatura_media": range(21, 29),
        "humedad_media": range(51, 59),
        "precipitacion_total_mm": range(1, 9),
    })


class TestFeatures(unittest.TestCase):
    def test_lags_variables_y_entrada_desordenada(self):
        resultado = generar_features(ejemplo().iloc[::-1])
        for variable in ("casos_confirmados", "temperatura_media", "humedad_media", "precipitacion_total_mm"):
            for k in (2, 3, 4):
                self.assertEqual(resultado.features.loc[4, f"{variable}_lag{k}"], ejemplo().loc[4-k, variable])
        self.assertFalse(resultado.continuidad.iloc[3])
        self.assertTrue(resultado.continuidad.iloc[4])

    def test_separacion_municipios_y_enfermedades(self):
        df = pd.concat([ejemplo(), ejemplo("B", base=100), ejemplo(enfermedad="malaria", base=200)])
        r = generar_features(df)
        for municipio, enfermedad, esperado in [("a", "dengue", 30), ("b", "dengue", 130), ("a", "malaria", 230)]:
            mascara = (r.claves.municipio == municipio) & (r.claves.enfermedad == enfermedad) & (r.claves.semana_epidemiologica == 5)
            self.assertEqual(r.features.loc[mascara, "casos_confirmados_lag2"].iloc[0], esperado)

    def test_semana_faltante_no_desplaza_lags_ni_inventa_filas(self):
        r = generar_features(ejemplo().drop(index=2))
        self.assertEqual(len(r.features), 7)
        fila5 = r.claves.index[r.claves.semana_epidemiologica == 5][0]
        self.assertTrue(pd.isna(r.features.loc[fila5, "casos_confirmados_lag2"]))
        self.assertEqual(r.features.loc[fila5, "casos_confirmados_lag3"], 20)
        self.assertTrue(pd.isna(r.features.loc[fila5, "casos_confirmados_media_movil_2sem"]))
        self.assertFalse(r.continuidad.loc[fila5])

    def test_medias_solo_pasado_y_opcion_cierre(self):
        r = generar_features(ejemplo())
        for w, esperado in [(2, 35), (3, 30), (4, 25)]:
            self.assertEqual(r.features.loc[4, f"casos_confirmados_media_movil_{w}sem"], esperado)
        self.assertTrue(pd.isna(r.features.loc[2, "casos_confirmados_media_movil_4sem"]))
        cierre = generar_features(ejemplo(), incluir_semana_actual=True)
        self.assertEqual(cierre.features.loc[4, "casos_confirmados_media_movil_2sem"], 45)
        self.assertEqual(cierre.features.loc[4, "casos_confirmados"], 50)

    def test_valores_faltantes_no_se_imputan(self):
        df = ejemplo()
        df.loc[2, "temperatura_media"] = float("nan")
        r = generar_features(df)
        self.assertTrue(pd.isna(r.features.loc[4, "temperatura_media_lag2"]))
        self.assertTrue(pd.isna(r.features.loc[4, "temperatura_media_media_movil_2sem"]))

    def test_no_leakage_objetivos_columnas_precalculadas_y_futuro(self):
        df = ejemplo()
        df["casos_dengue_t_mas_3"] = 999
        df["temperatura_media_lag2"] = -999
        df["otra_variable_futura"] = 999
        original = df.copy(deep=True)
        r = generar_features(df)
        self.assertEqual(list(r.objetivos), ["casos_dengue_t_mas_3"])
        self.assertFalse(set(r.objetivos) & set(r.features))
        self.assertNotIn("otra_variable_futura", r.features)
        self.assertNotIn("casos_confirmados", r.features)
        modificado = df.copy()
        modificado.loc[4:, ["casos_confirmados", "temperatura_media", "humedad_media", "precipitacion_total_mm"]] = 10000
        modificado["casos_dengue_t_mas_3"] = -100
        assert_frame_equal(r.features.iloc[:5], generar_features(modificado).features.iloc[:5])
        assert_frame_equal(df, original)

    def test_cruce_de_anio_iso(self):
        df = ejemplo().iloc[:5].copy()
        df["anio"] = [2025, 2025, 2026, 2026, 2026]
        df["semana_epidemiologica"] = [51, 52, 1, 2, 3]
        r = generar_features(df)
        self.assertEqual(r.features.loc[4, "casos_confirmados_lag4"], 10)
        self.assertTrue(r.continuidad.loc[4])

    def test_validaciones_y_bloques_malaria(self):
        for columna, valor in [("semana_epidemiologica", 54), ("semana_epidemiologica", 2.5), ("municipio", None), ("enfermedad", " ")]:
            with self.subTest(columna=columna, valor=valor):
                df = ejemplo().astype({columna: object})
                df.loc[0, columna] = valor
                with self.assertRaises(ValueError):
                    generar_features(df)
        with self.assertRaises(ValueError):
            generar_features(pd.concat([ejemplo(), ejemplo()]))
        with self.assertRaises(ValueError):
            generar_features(ejemplo().assign(se_inicio=1, se_fin=5))

    def test_variables_opcionales(self):
        df = ejemplo().drop(columns=["temperatura_media", "humedad_media", "precipitacion_total_mm"])
        self.assertEqual(generar_features(df).features.shape, (8, 6))
        with self.assertRaises(ValueError):
            generar_features(df.drop(columns="enfermedad"))

    def test_entrada_vacia_error_explicito(self):
        with self.assertRaisesRegex(ValueError, "vacío"):
            generar_features(ejemplo().iloc[:0])

    def test_cierre_no_utiliza_semanas_futuras(self):
        df = ejemplo()
        original = generar_features(df, incluir_semana_actual=True)
        df.loc[5:, ["casos_confirmados", "temperatura_media", "humedad_media", "precipitacion_total_mm"]] = 10000
        cambiado = generar_features(df, incluir_semana_actual=True)
        assert_frame_equal(original.features.iloc[:5], cambiado.features.iloc[:5])

    def test_medias_y_lags_reales_contra_calendario(self):
        datos = pd.read_csv(DATASET_DENGUE)
        r = generar_features(datos)
        # Referencia independiente a partir de las observaciones del CSV,
        # sin consumir sus lags precalculados ni otras filas del resultado.
        referencia = {}
        for _, fila in datos.iterrows():
            lunes = date.fromisocalendar(int(fila.anio), int(fila.semana_epidemiologica), 1)
            referencia[(fila.municipio.strip().casefold(), lunes)] = fila
        for i, clave in r.claves.iterrows():
            lunes = clave.fecha_semana.date()
            for variable in ("casos_dengue", "temperatura_media", "humedad_media", "precipitacion_total_mm"):
                for k in (2, 3, 4):
                    anterior = referencia.get((clave.municipio, lunes - timedelta(weeks=k)))
                    actual = r.features.loc[i, f"{variable}_lag{k}"]
                    if anterior is None:
                        self.assertTrue(pd.isna(actual))
                    else:
                        self.assertAlmostEqual(actual, anterior[variable])
                for w in (2, 3, 4):
                    anteriores = [referencia.get((clave.municipio, lunes - timedelta(weeks=k))) for k in range(1, w + 1)]
                    actual = r.features.loc[i, f"{variable}_media_movil_{w}sem"]
                    if any(fila is None for fila in anteriores):
                        self.assertTrue(pd.isna(actual))
                    else:
                        self.assertAlmostEqual(actual, sum(fila[variable] for fila in anteriores) / w)

    def test_interfaz_para_modelo_features_numericas_y_objetivos_alineados(self):
        r = cargar_features()
        self.assertTrue(all(pd.api.types.is_numeric_dtype(t) for t in r.features.dtypes))
        self.assertTrue(r.features.index.equals(r.claves.index))
        self.assertTrue(r.features.index.equals(r.continuidad.index))
        self.assertTrue(r.features.index.equals(r.objetivos.index))
        for horizonte, filas in ((3, 168), (4, 140)):
            objetivo = r.objetivos[f"casos_dengue_t_mas_{horizonte}"]
            utiles = r.features.notna().all(axis=1) & objetivo.notna()
            X = r.features.loc[utiles]
            y = objetivo.loc[utiles]
            self.assertEqual(X.shape, (filas, 24))
            self.assertEqual(y.shape, (filas,))
            self.assertTrue(X.index.equals(y.index))
            self.assertEqual(X.to_numpy(dtype=float).shape, (filas, 24))

    def test_dataset_real_sin_modificaciones(self):
        antes = hashlib.sha256(DATASET_DENGUE.read_bytes()).hexdigest()
        r = cargar_features()
        self.assertEqual(r.features.shape, (364, 24))
        self.assertEqual(r.claves.municipio.nunique(), 28)
        self.assertEqual(set(r.claves.enfermedad), {"dengue"})
        self.assertEqual(len(r.objetivos.columns), 3)
        self.assertEqual(r.features["casos_dengue_lag4"].isna().sum(), 112)
        self.assertEqual(hashlib.sha256(DATASET_DENGUE.read_bytes()).hexdigest(), antes)


class TestIntegracionTemporal(unittest.TestCase):
    """Ejecuta el contrato de entrega del documento, sin editar el pipeline."""

    @classmethod
    def setUpClass(cls):
        raiz = DATASET_DENGUE.parents[2]
        documento = (raiz / "docs/task_011_features.md").read_text(encoding="utf-8")
        bloque = documento.split("```python\n# EJEMPLO_REPRODUCIBLE_TASK_011\n", 1)[1].split("```", 1)[0]
        # Simula la ubicación de un consumidor en scripts/; no crea ese archivo.
        namespace = {"__file__": str(raiz / "scripts/consumidor_task_011.py")}
        with redirect_stdout(io.StringIO()):
            exec(compile(bloque, str(raiz / "docs/task_011_features.md"), "exec"), namespace)
        cls.ejemplo = namespace

    def partir(self, horizonte, *, completas=False, retraso=0):
        return self.ejemplo["preparar_particion"](
            self.ejemplo["resultado"], horizonte, "2026-02-23",
            exigir_historia_completa=completas, retraso_semanas=retraso,
        )

    def test_ejemplo_importable_y_reproducible_para_ambos_horizontes(self):
        for h, n_train, n_test in ((3, 28, 56), (4, 56, 28)):
            with self.subTest(horizonte=h):
                p = self.ejemplo["particiones"][h]
                self.assertEqual(p["train"]["X"].shape, (n_train, 24))
                self.assertEqual(p["test"]["X"].shape, (n_test, 24))

    def test_fechas_explicitas_y_municipios_de_cada_fecha_no_se_mezclan(self):
        r = self.ejemplo["resultado"]
        corte = pd.Timestamp("2026-02-23")
        for h in (3, 4):
            p = self.partir(h)
            self.assertTrue(p["train"]["fecha_semana"].lt(corte).all())
            self.assertTrue(p["test"]["fecha_semana"].ge(corte).all())
            self.assertFalse(set(p["train"]["fecha_semana"]) & set(p["test"]["fecha_semana"]))
            mascara = p["mascaras"]
            self.assertTrue((mascara["train"].astype(int) + mascara["test"].astype(int) + mascara["excluido"].astype(int)).eq(1).all())
            for _, indices in r.claves.groupby("fecha_semana").groups.items():
                # Con el panel completo actual, los 28 municipios tienen
                # exactamente la misma asignación train/test/excluido.
                self.assertEqual(len(indices), 28)
                for nombre in ("train", "test", "excluido"):
                    self.assertEqual(mascara[nombre].loc[indices].nunique(), 1)

    def test_objetivo_debe_haber_cerrado_y_no_solo_fecha_del_predictor(self):
        r = self.ejemplo["resultado"]
        corte = pd.Timestamp("2026-02-23")
        for h in (3, 4):
            p = self.partir(h)
            train = p["mascaras"]["train"]
            disponibles = p["fecha_disponible"]
            esperadas = r.claves.fecha_semana + pd.Timedelta(weeks=h + 1)
            pd.testing.assert_series_equal(disponibles, esperadas)
            self.assertTrue(disponibles.loc[train].le(corte).all())
            # Incluye el caso de cierre exactamente en la fecha de corte.
            self.assertTrue((train & disponibles.eq(corte)).any())
            sin_cerrar = r.claves.fecha_semana.lt(corte) & disponibles.gt(corte)
            self.assertTrue(sin_cerrar.any())
            self.assertFalse(train.loc[sin_cerrar].any())
            self.assertTrue(p["mascaras"]["excluido"].loc[sin_cerrar].all())

    def test_retraso_de_publicacion_restringe_el_entrenamiento(self):
        for h in (3, 4):
            sin_retraso = self.partir(h)
            retrasado = self.partir(h, retraso=1)
            base = sin_retraso["mascaras"]["train"]
            nuevo = retrasado["mascaras"]["train"]
            self.assertTrue((~nuevo | base).all())
            self.assertLess(nuevo.sum(), base.sum())
            pd.testing.assert_series_equal(
                retrasado["fecha_disponible"],
                sin_retraso["fecha_disponible"] + pd.Timedelta(weeks=1),
            )

    def test_alineacion_y_objetivos_fuera_de_X_tras_partir(self):
        r = self.ejemplo["resultado"]
        for h in (3, 4):
            p = self.partir(h)
            for nombre in ("train", "test"):
                parte = p[nombre]
                mascara = p["mascaras"][nombre]
                self.assertTrue(parte["X"].index.equals(parte["y"].index))
                self.assertTrue(parte["X"].index.equals(parte["fecha_semana"].index))
                assert_frame_equal(parte["X"], r.features.loc[mascara])
                pd.testing.assert_series_equal(parte["y"], r.objetivos.loc[mascara, f"casos_dengue_t_mas_{h}"])
                self.assertFalse(set(r.objetivos) & set(parte["X"]))
                self.assertFalse(parte["y"].isna().any())

    def test_t4_estricto_sin_train_y_alternativa_con_nan_explicitos(self):
        estricto = self.partir(4, completas=True)
        self.assertTrue(estricto["train"]["X"].empty)
        parcial = self.partir(4)
        self.assertEqual(len(parcial["train"]["X"]), 56)
        self.assertTrue(parcial["train"]["X"].isna().any().any())
        self.assertFalse(parcial["train"]["X"].isna().all(axis=1).any())
        # Primeras semanas completamente desconocidas siguen excluidas.
        r = self.ejemplo["resultado"]
        sin_historia = r.features.isna().all(axis=1)
        self.assertTrue(parcial["mascaras"]["excluido"].loc[sin_historia].all())

    @unittest.skipUnless(pd.__version__ == "2.2.3", "Pendiente: pandas 2.2.3 no está disponible en este intérprete.")
    def test_compatibilidad_pandas_223(self):
        r = cargar_features()
        self.assertEqual(r.features.shape, (364, 24))
        for h in (3, 4):
            p = self.partir(h)
            self.assertFalse(p["train"]["X"].empty)
            self.assertTrue(all(pd.api.types.is_numeric_dtype(t) for t in p["train"]["X"].dtypes))
        nullable = ejemplo().astype({"casos_confirmados": "Int64"})
        nullable.loc[2, "casos_confirmados"] = pd.NA
        calculado = generar_features(nullable)
        self.assertTrue(pd.isna(calculado.features.loc[4, "casos_confirmados_lag2"]))

    @unittest.skipUnless(importlib.util.find_spec("xgboost") is not None, "Pendiente: XGBoost no está instalado; no se instalan dependencias.")
    def test_integracion_xgboost_dmatrix_entrenamiento_y_prediccion(self):
        import xgboost as xgb

        for h in (3, 4):
            with self.subTest(horizonte=h):
                p = self.partir(h, completas=(h == 3))
                train = xgb.DMatrix(p["train"]["X"], label=p["train"]["y"], missing=float("nan"))
                test = xgb.DMatrix(p["test"]["X"], missing=float("nan"))
                modelo = xgb.train(
                    {"objective": "reg:squarederror", "max_depth": 2,
                     "tree_method": "hist", "nthread": 1, "seed": 11},
                    train, num_boost_round=3,
                )
                predicciones = modelo.predict(test)
                self.assertEqual(len(predicciones), len(p["test"]["y"]))
                self.assertTrue(all(math.isfinite(float(v)) for v in predicciones))


if __name__ == "__main__":
    unittest.main()
