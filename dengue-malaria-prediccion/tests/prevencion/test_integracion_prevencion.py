"""TASK-024/025: PostgreSQL/PostGIS y JWT reales, solo en BD de pruebas explícita.

Datos de ejemplo exclusivos de tests; nunca se usan como respuestas productivas.
No instala dependencias, crea esquema ni aplica migraciones. Cada test revierte
su transacción exterior, incluidos commits de login mediante savepoints.
"""

import importlib.util
import json
import os
import unittest
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

DEPENDENCIAS = ("fastapi", "sqlalchemy", "geoalchemy2", "psycopg2", "httpx", "bcrypt", "jose")
FALTANTES = [p for p in DEPENDENCIAS if importlib.util.find_spec(p) is None]
URL_PRUEBAS = os.getenv("GATOBYTE_TEST_DATABASE_URL")
MOTIVO = ("Dependencias ausentes: " + ", ".join(FALTANTES)) if FALTANTES else (
    "Defina GATOBYTE_TEST_DATABASE_URL de una BD exclusiva de pruebas migrada."
)


@unittest.skipIf(bool(FALTANTES) or not URL_PRUEBAS, MOTIVO)
class TestIntegracionPrevencion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entorno = patch.dict(os.environ, {
            "DATABASE_URL": URL_PRUEBAS,
            "SECRET_KEY": "clave-exclusiva-tests-prevencion-32-caracteres",
            "ENVIRONMENT": "testing",
            "ALGORITHM": "HS256",
        })
        cls.entorno.start()
        cls.addClassCleanup(cls.entorno.stop)
        from sqlalchemy import create_engine
        from app.core.config import get_settings
        get_settings.cache_clear()
        cls.addClassCleanup(get_settings.cache_clear)
        cls.engine = create_engine(URL_PRUEBAS)
        cls.addClassCleanup(cls.engine.dispose)
        # Si el entorno está presente pero roto, el test FALLA: no se omite.
        from app.main import app
        cls.app = app

    def setUp(self):
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session
        from app.core.database import get_db
        from app.etl.seed_catalogo import seed
        from app.models import Modelo

        conexion = self.engine.connect()
        self.addCleanup(conexion.close)
        transaccion = conexion.begin()
        self.addCleanup(transaccion.rollback)
        self.db = Session(bind=conexion, join_transaction_mode="create_savepoint")
        self.addCleanup(self.db.close)
        self.catalogo = seed(db=self.db)
        self.municipios = list(self.catalogo["municipios"].values())
        self.dengue = self.catalogo["enfermedades"]["dengue"]
        self.malaria = self.catalogo["enfermedades"]["malaria"]
        self.ahora = datetime.now(timezone.utc).replace(microsecond=0)
        self.modelos = {}
        for h in (3, 4):
            ruta = Path(__file__).resolve().parents[2] / "app/ml/artifacts" / f"baseline_dengue_t{h}_v1_metadata.json"
            metadata = json.loads(ruta.read_text(encoding="utf-8"))
            modelo = Modelo(nombre=metadata["nombre"], version="test",
                enfermedad_id=self.dengue.id, fecha_entrenamiento=self.ahora,
                metricas_entrenamiento=metadata)
            self.db.add(modelo)
            self.db.flush()
            self.modelos[h] = modelo

        def sesion():
            yield self.db

        anteriores = dict(self.app.dependency_overrides)
        self.addCleanup(self._restaurar_overrides, anteriores)
        self.app.dependency_overrides[get_db] = sesion
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def _restaurar_overrides(self, anteriores):
        self.app.dependency_overrides.clear()
        self.app.dependency_overrides.update(anteriores)

    def cabecera(self, rol="sedes", municipio=None, login=False):
        from app.core.security import crear_access_token, hash_password
        from app.models import Rol, Usuario
        from sqlalchemy import select
        fila_rol = self.db.execute(select(Rol).where(Rol.nombre == rol)).scalar_one_or_none()
        if fila_rol is None:
            fila_rol = Rol(nombre=rol)
            self.db.add(fila_rol)
            self.db.flush()
        usuario = Usuario(email=f"{rol}.{uuid4().hex}@test.local",
            password_hash=hash_password("ClaveSoloTest123!"), rol_id=fila_rol.id,
            municipio_asignado_id=municipio)
        self.db.add(usuario)
        self.db.flush()
        if login:
            r = self.client.post("/auth/login", data={"username": usuario.email, "password": "ClaveSoloTest123!"})
            self.assertEqual(r.status_code, 200, r.text)
            token = r.json()["access_token"]
        else:
            token = crear_access_token(usuario.id, rol)
        return {"Authorization": f"Bearer {token}"}

    def prediccion(self, municipio=0, h=3, probabilidad=80, generada=None, dias=None,
                   metadata="normal", enfermedad=None):
        from app.ml.prediccion import clasificar_nivel_riesgo
        from app.models import Prediccion
        modelo = self.modelos[h]
        if metadata != "normal":
            modelo.metricas_entrenamiento = metadata
        generada = generada or self.ahora
        fila = Prediccion(municipio_id=self.municipios[municipio].id,
            enfermedad_id=(enfermedad or self.dengue).id, modelo_id=modelo.id,
            fecha_generacion=generada,
            fecha_estimada_riesgo=generada.astimezone(timezone.utc).date() + timedelta(days=dias or 7*h),
            nivel_riesgo=clasificar_nivel_riesgo(probabilidad), probabilidad_pct=probabilidad,
            nivel_confianza="alto", variables_explicativas=[{"variable": "dato_de_prueba", "peso": 0.1}])
        self.db.add(fila)
        self.db.flush()
        return fila

    def campanas(self, **kw):
        return self.client.get("/campanas/priorizacion", headers=self.cabecera(**kw))

    def recursos(self, municipio=None, asignado=None, **kw):
        mid = self.municipios[0].id if municipio is None else municipio
        return self.client.get(f"/municipios/{mid}/recursos", headers=self.cabecera(rol=kw.pop("rol", "admin"), municipio=asignado, **kw))

    def test_ranking_riesgo(self):
        for i, prob in enumerate((10, 50, 80)):
            self.prediccion(i, probabilidad=prob)
        r = self.campanas()
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual([p["nivel_riesgo"] for p in r.json()], ["alto", "medio", "bajo"])
        self.assertEqual([p["posicion"] for p in r.json()], [1, 2, 3])

    def test_fecha_antes_de_probabilidad(self):
        self.prediccion(0, probabilidad=90)
        p = self.prediccion(1, generada=self.ahora-timedelta(days=1))
        self.assertEqual(self.campanas().json()[0]["prediccion_id"], p.id)

    def test_desempate_probabilidad(self):
        self.prediccion(0, probabilidad=80)
        p = self.prediccion(1, probabilidad=90)
        self.assertEqual(self.campanas().json()[0]["prediccion_id"], p.id)

    def test_desempate_id_municipal(self):
        self.prediccion(1)
        self.prediccion(0)
        self.assertEqual([p["municipio_id"] for p in self.campanas().json()], sorted(m.id for m in self.municipios[:2]))

    def test_sin_predicciones_vacio(self):
        r = self.campanas()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_municipios_sin_prediccion_se_excluyen(self):
        self.prediccion()
        self.assertEqual(len(self.campanas().json()), 1)

    def test_t4_excluido_de_ambos(self):
        self.prediccion(h=4)
        self.assertEqual(self.campanas().json(), [])
        self.assertEqual(self.recursos().status_code, 404)

    def test_vencida_excluida_de_ambos(self):
        self.prediccion(generada=self.ahora-timedelta(days=22))
        self.assertEqual(self.campanas().json(), [])
        self.assertEqual(self.recursos().status_code, 404)

    def test_fecha_objetivo_hoy_incluida(self):
        p = self.prediccion(generada=self.ahora-timedelta(days=21))
        self.assertEqual(self.campanas().json()[0]["prediccion_id"], p.id)

    def test_metadata_incompleta_excluida(self):
        for metadata in ({}, {"enfermedad": "dengue"}, {"horizonte_semanas": 3}):
            with self.subTest(metadata=metadata):
                self.prediccion(metadata=metadata)
                self.assertEqual(self.campanas().json(), [])
                self.assertEqual(self.recursos().status_code, 404)

    def test_metadata_no_numerica_o_invalida(self):
        for metadata in (None, [], "invalida", {"enfermedad": "dengue", "horizonte_semanas": "3"}, {"enfermedad": "dengue", "horizonte_semanas": True}):
            with self.subTest(metadata=metadata):
                self.prediccion(metadata=metadata)
                self.assertEqual(self.campanas().json(), [])
                self.assertEqual(self.recursos().status_code, 404)

    def test_fecha_contradictoria_excluida(self):
        self.prediccion(dias=22)
        self.assertEqual(self.campanas().json(), [])
        self.assertEqual(self.recursos().status_code, 404)

    def test_enfermedad_contradictoria_excluida(self):
        self.prediccion(enfermedad=self.malaria)
        self.assertEqual(self.campanas().json(), [])
        self.assertEqual(self.recursos().status_code, 404)

    def test_filtra_antes_de_seleccionar_ultima(self):
        valida = self.prediccion(generada=self.ahora-timedelta(days=1))
        self.prediccion(h=4)
        self.assertEqual(self.campanas().json()[0]["prediccion_id"], valida.id)
        self.assertEqual(self.recursos().json()["prediccion_id"], valida.id)

    def test_ultima_elegible_y_desempate_id(self):
        self.prediccion(probabilidad=90, generada=self.ahora-timedelta(days=1))
        self.prediccion(probabilidad=80)
        ultima = self.prediccion(probabilidad=70)
        self.assertEqual(self.campanas().json()[0]["prediccion_id"], ultima.id)

    def test_fechas_se_interpretan_en_utc(self):
        local = datetime.combine(self.ahora.date()-timedelta(days=1), time(23, 30), tzinfo=timezone(timedelta(hours=-4)))
        p = self.prediccion(generada=local)
        self.assertEqual(self.recursos().json()["fecha_estimada_riesgo"], p.fecha_estimada_riesgo.isoformat())

    def test_recursos_alto(self):
        self.prediccion(probabilidad=80)
        r = self.recursos()
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["nivel_atencion"], "PRIORITARIO")
        self.assertEqual(len(r.json()["recomendaciones"]), 4)

    def test_recursos_medio(self):
        self.prediccion(probabilidad=50)
        self.assertEqual(self.recursos().json()["nivel_atencion"], "PREVENTIVO")

    def test_recursos_bajo(self):
        self.prediccion(probabilidad=10)
        self.assertEqual(self.recursos().json()["nivel_atencion"], "RUTINARIO")

    def test_municipio_inexistente_vs_sin_prediccion(self):
        inexistente = self.recursos(municipio=2147483647)
        sin_datos = self.recursos()
        self.assertEqual(inexistente.status_code, 404)
        self.assertEqual(sin_datos.status_code, 404)
        self.assertNotEqual(inexistente.json()["detail"], sin_datos.json()["detail"])

    def test_roles_no_autorizados(self):
        for rol in ("autoridad", "epidemiologo"):
            self.assertEqual(self.campanas(rol=rol).status_code, 403)
            self.assertEqual(self.recursos(rol=rol).status_code, 403)
        self.assertEqual(self.campanas(rol="admin").status_code, 403)
        self.assertEqual(self.recursos(rol="sedes").status_code, 403)

    def test_coordinador_solo_ve_su_municipio(self):
        self.prediccion(0)
        self.prediccion(1)
        mid = self.municipios[0].id
        r = self.campanas(rol="coordinador_municipal", municipio=mid)
        self.assertEqual([p["municipio_id"] for p in r.json()], [mid])
        self.assertEqual(self.recursos(rol="coordinador_municipal", asignado=mid).status_code, 200)
        ajeno = self.recursos(municipio=self.municipios[1].id, rol="coordinador_municipal")
        self.assertEqual(ajeno.status_code, 403)

    def test_coordinador_ajeno_bloqueado(self):
        headers = self.cabecera("coordinador_municipal", self.municipios[1].id)
        r = self.client.get(f"/municipios/{self.municipios[0].id}/recursos", headers=headers)
        self.assertEqual(r.status_code, 403)

    def test_coordinador_sin_asignacion(self):
        self.assertEqual(self.campanas(rol="coordinador_municipal").status_code, 403)
        self.assertEqual(self.recursos(rol="coordinador_municipal").status_code, 403)

    def test_sin_token(self):
        for ruta in ("/campanas/priorizacion", f"/municipios/{self.municipios[0].id}/recursos"):
            self.assertEqual(self.client.get(ruta).status_code, 401)

    def test_login_real_y_contratos_json(self):
        self.prediccion()
        r = self.recursos(login=True)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["horizonte_semanas"], 3)
        self.assertEqual(r.json()["enfermedad"], "dengue")
        self.assertIn("No constituyen protocolos oficiales de SEDES", r.json()["nota"])
        self.assertNotIn("variables_explicativas", r.json())

    def test_router_y_validacion_id(self):
        rutas = self.app.openapi()["paths"]
        self.assertIn("/campanas/priorizacion", rutas)
        self.assertIn("/municipios/{municipio_id}/recursos", rutas)
        r = self.client.get("/municipios/no-numero/recursos", headers=self.cabecera("admin"))
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
