"""TASK-024/025: reglas puras y contratos; ejemplos exclusivos de pruebas."""

import unittest
from datetime import date, datetime, timezone

from app.services.reglas_prevencion import alcance_municipal, priorizar, recomendar


class TestReglas(unittest.TestCase):
    def fila(self, municipio=1, riesgo="alto", dia=20, probabilidad=80):
        return dict(municipio_id=municipio, nivel_riesgo=riesgo,
                    fecha_estimada_riesgo=date(2026, 11, dia),
                    probabilidad_pct=probabilidad)

    def test_riesgo_antes_de_fecha(self):
        filas = [self.fila(1, "bajo", 1, 10), self.fila(2, "medio", 2, 50),
                 self.fila(3, "alto", 20, 80)]
        self.assertEqual([f["municipio_id"] for f in priorizar(filas)], [3, 2, 1])

    def test_fecha_antes_de_probabilidad(self):
        filas = [self.fila(1, dia=20, probabilidad=90), self.fila(2, dia=15)]
        self.assertEqual(priorizar(filas)[0]["municipio_id"], 2)

    def test_desempate_probabilidad(self):
        self.assertEqual(priorizar([self.fila(1), self.fila(2, probabilidad=90)])[0]["municipio_id"], 2)

    def test_desempate_id_y_posiciones(self):
        filas = priorizar([self.fila(3), self.fila(1), self.fila(2)])
        self.assertEqual([f["municipio_id"] for f in filas], [1, 2, 3])
        self.assertEqual([f["posicion"] for f in filas], [1, 2, 3])

    def test_vacio(self):
        self.assertEqual(priorizar([]), [])

    def test_no_muta_entrada(self):
        fila = self.fila()
        priorizar([fila])
        self.assertNotIn("posicion", fila)

    def test_recomendacion_alta(self):
        r = recomendar("alto")
        self.assertEqual(r["nivel_atencion"], "PRIORITARIO")
        self.assertEqual(len(r["recomendaciones"]), 4)
        self.assertIn("Evaluar disponibilidad de insumos.", r["recomendaciones"])

    def test_recomendacion_media(self):
        r = recomendar("medio")
        self.assertEqual(r["nivel_atencion"], "PREVENTIVO")
        self.assertEqual(len(r["recomendaciones"]), 4)

    def test_recomendacion_baja(self):
        r = recomendar("bajo")
        self.assertEqual(r["nivel_atencion"], "RUTINARIO")
        self.assertEqual(len(r["recomendaciones"]), 3)

    def test_nota_y_no_inventarios(self):
        for nivel in ("alto", "medio", "bajo"):
            r = recomendar(nivel)
            self.assertIn("No constituyen protocolos oficiales de SEDES", r["nota"])
            self.assertEqual(set(r), {"nivel_atencion", "recomendaciones", "nota"})
        recomendar("alto")["recomendaciones"].clear()
        self.assertEqual(len(recomendar("alto")["recomendaciones"]), 4)

    def test_sin_datos_no_es_bajo(self):
        for nivel in (None, "", "desconocido"):
            with self.assertRaises(KeyError):
                recomendar(nivel)

    def test_coordinador_limitado(self):
        self.assertEqual(alcance_municipal("coordinador_municipal", 3), 3)
        self.assertEqual(alcance_municipal("coordinador_municipal", 3, 3), 3)

    def test_coordinador_ajeno(self):
        with self.assertRaises(PermissionError):
            alcance_municipal("coordinador_municipal", 3, 4)

    def test_coordinador_sin_asignacion(self):
        for solicitado in (None, 1):
            with self.assertRaises(PermissionError):
                alcance_municipal("coordinador_municipal", None, solicitado)

    def test_admin_y_sedes_sin_filtro_municipal(self):
        self.assertIsNone(alcance_municipal("admin", None, 8))
        self.assertIsNone(alcance_municipal("sedes", None))


class TestSchemas(unittest.TestCase):
    def setUp(self):
        from app.schemas.prevencion import PrioridadCampana, RecursosMunicipio
        self.campana = PrioridadCampana
        self.recursos = RecursosMunicipio
        self.datos = dict(
            prediccion_id=10, municipio_id=1, municipio="MUNICIPIO DE PRUEBA",
            departamento_id=1, departamento="DEPARTAMENTO DE PRUEBA",
            enfermedad_id=1, enfermedad="dengue", horizonte_semanas=3,
            probabilidad_pct=80, nivel_riesgo="alto", nivel_confianza="alto",
            fecha_generacion=datetime(2026, 11, 1, tzinfo=timezone.utc),
            fecha_estimada_riesgo=date(2026, 11, 22),
        )

    def test_json_campana(self):
        r = self.campana(**self.datos, posicion=1).model_dump(mode="json")
        self.assertEqual(r["fecha_estimada_riesgo"], "2026-11-22")
        self.assertEqual(r["probabilidad_pct"], 80)
        self.assertNotIn("variables_explicativas", r)

    def test_json_recursos(self):
        r = self.recursos(**self.datos, **recomendar("alto")).model_dump(mode="json")
        self.assertEqual(r["nivel_atencion"], "PRIORITARIO")

    def test_solo_dengue_t3(self):
        from pydantic import ValidationError
        for cambio in ({"horizonte_semanas": 4}, {"enfermedad": "malaria"}):
            with self.assertRaises(ValidationError):
                self.campana(**(self.datos | cambio), posicion=1)

    def test_probabilidad_y_posicion_validas(self):
        from pydantic import ValidationError
        for valor in (-1, 101, float("nan"), float("inf")):
            with self.assertRaises(ValidationError):
                self.campana(**(self.datos | {"probabilidad_pct": valor}), posicion=1)
        with self.assertRaises(ValidationError):
            self.campana(**self.datos, posicion=0)


if __name__ == "__main__":
    unittest.main()
