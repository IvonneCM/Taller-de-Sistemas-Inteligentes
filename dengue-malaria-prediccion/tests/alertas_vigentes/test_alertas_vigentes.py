"""Extensión compatible de TASK-030: HTTP/PostgreSQL real, solo BD aislada.

No ejecuta seeds ni migraciones. Fixtures ficticias solo dentro de transacciones
revertidas en la base explícita GATOBYTE_TEST_DATABASE_URL, nunca la del .env.
"""

import importlib.util
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

FALTANTES = [p for p in ("fastapi", "sqlalchemy", "psycopg2", "geoalchemy2", "bcrypt", "httpx", "jose") if importlib.util.find_spec(p) is None]
URL = os.getenv("GATOBYTE_TEST_DATABASE_URL")


@unittest.skipIf(bool(FALTANTES) or not URL, "Requiere dependencias y GATOBYTE_TEST_DATABASE_URL de una BD exclusiva migrada.")
class TestAlertasVigentes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy.engine import make_url
        url = make_url(URL)
        if url.host not in ("127.0.0.1", "localhost") or url.database != "gatobyte_task024025_test":
            raise RuntimeError("Esta suite solo admite la base local exclusiva de testing.")
        cls.entorno = patch.dict(os.environ, {
            "DATABASE_URL": URL, "SECRET_KEY": "clave-solo-pruebas-alertas-vigentes-32",
            "ENVIRONMENT": "testing", "ALGORITHM": "HS256", "LOG_LEVEL": "WARNING",
        })
        cls.entorno.start()
        cls.addClassCleanup(cls.entorno.stop)
        from app.core.config import get_settings
        get_settings.cache_clear()
        cls.addClassCleanup(get_settings.cache_clear)
        from sqlalchemy import create_engine
        from app.main import app
        cls.app = app
        cls.engine = create_engine(URL)
        cls.addClassCleanup(cls.engine.dispose)

    def setUp(self):
        from sqlalchemy.orm import Session
        from app.models import Departamento, Enfermedad, Modelo, Municipio
        from app.core.database import get_db
        from fastapi.testclient import TestClient
        self.connection = self.engine.connect()
        self.addCleanup(self.connection.close)
        transaction = self.connection.begin()
        self.addCleanup(transaction.rollback)
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        self.addCleanup(self.db.close)
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        # Catálogo exclusivo de tests, sin llamar a ningún seed del proyecto.
        dep = Departamento(nombre="DEPARTAMENTO-TEST-" + uuid4().hex)
        self.enfermedad = Enfermedad(nombre="enfermedad-test-" + uuid4().hex)
        self.db.add_all([dep, self.enfermedad])
        self.db.flush()
        self.municipios = [Municipio(nombre="MUNICIPIO-TEST-"+str(i), departamento_id=dep.id,
            geometria="MULTIPOLYGON(((0 0,1 0,1 1,0 1,0 0)))") for i in range(3)]
        self.modelo = Modelo(nombre="MODELO-TEST", version="test", enfermedad_id=self.enfermedad.id, fecha_entrenamiento=self.now)
        self.db.add_all([*self.municipios, self.modelo])
        self.db.flush()
        self.previous = dict(self.app.dependency_overrides)
        self.addCleanup(self.restore)
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def restore(self):
        self.app.dependency_overrides.clear()
        self.app.dependency_overrides.update(self.previous)

    def prediction(self, municipio=0, age=0, dias=21, variables=None):
        from app.models import Prediccion
        fecha = self.now - timedelta(days=age)
        p = Prediccion(municipio_id=self.municipios[municipio].id,
            enfermedad_id=self.enfermedad.id, modelo_id=self.modelo.id,
            fecha_generacion=fecha, fecha_estimada_riesgo=fecha.date()+timedelta(days=dias),
            nivel_riesgo="alto", probabilidad_pct=80, nivel_confianza="alto",
            variables_explicativas=variables if variables is not None else [{"variable": "variable_test", "peso": -0.2}])
        self.db.add(p)
        self.db.flush()
        return p

    def alert(self, p, justification="Justificación exclusiva de test.", offset=0):
        from app.models import Alerta
        a = Alerta(prediccion_id=p.id, umbral_aplicado=70,
                   fecha_emision=self.now+timedelta(seconds=offset), justificacion=justification)
        self.db.add(a)
        self.db.flush()
        return a

    def headers(self, role="sedes"):
        from sqlalchemy import select
        from app.models import Rol, Usuario
        from app.core.security import hash_password, crear_access_token
        r = self.db.execute(select(Rol).where(Rol.nombre==role)).scalar_one_or_none()
        if r is None:
            r = Rol(nombre=role)
            self.db.add(r)
            self.db.flush()
        u = Usuario(email=uuid4().hex+"@test.local", rol_id=r.id, password_hash=hash_password("SoloTest123!"))
        self.db.add(u)
        self.db.flush()
        return {"Authorization": "Bearer "+crear_access_token(u.id, role)}

    def get(self, vigente=True, **params):
        params.setdefault("enfermedad_id", self.enfermedad.id)
        if vigente is not None:
            params["solo_vigentes"] = str(vigente).lower()
        r = self.client.get("/alertas", params=params, headers=self.headers())
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_ultima_con_alerta_y_fecha_en_respuesta(self):
        p = self.prediction()
        a = self.alert(p)
        rows = self.get()
        self.assertEqual([r["id"] for r in rows], [a.id])
        self.assertEqual(rows[0]["fecha_estimada_riesgo"], p.fecha_estimada_riesgo.isoformat())

    def test_prediccion_nueva_sustituye_anterior(self):
        old = self.alert(self.prediction(age=1))
        new = self.alert(self.prediction(), offset=1)
        self.assertEqual([r["id"] for r in self.get()], [new.id])
        self.assertEqual({r["id"] for r in self.get(False)}, {old.id,new.id})

    def test_nueva_sin_alerta_invalida_la_anterior(self):
        self.alert(self.prediction(age=1))
        self.prediction()
        self.assertEqual(self.get(), [])
        self.assertEqual(len(self.get(False)), 1)

    def test_no_recurre_a_una_prediccion_antigua_si_la_ultima_vencio(self):
        self.alert(self.prediction(age=23,dias=28))
        self.prediction(age=22,dias=21)
        self.assertEqual(self.get(), [])

    def test_vencida(self):
        self.alert(self.prediction(age=22))
        self.assertEqual(self.get(), [])
        self.assertEqual(len(self.get(False)), 1)

    def test_fecha_objetivo_hoy_es_vigente(self):
        self.alert(self.prediction(age=21))
        self.assertEqual(len(self.get()), 1)

    def test_desempate_de_generacion_por_id(self):
        self.alert(self.prediction())
        self.prediction()
        self.assertEqual(self.get(), [])

    def test_distingue_municipios(self):
        a = self.alert(self.prediction())
        self.prediction(1)
        self.assertEqual([r["id"] for r in self.get()], [a.id])

    def test_nueva_sin_explicacion_tambien_sustituye_anterior(self):
        self.alert(self.prediction(age=1))
        self.prediction(variables=[])
        self.assertEqual(self.get(), [])

    def test_rechaza_justificacion_solo_espacios_blancos(self):
        self.alert(self.prediction(), justification="\t\n")
        self.assertEqual(self.get(), [])
        self.assertEqual(len(self.get(False)), 1)

    def test_variables_invalidas(self):
        for variables in ([], [{}], [{"variable":"", "peso":1}], [{"variable":"\t", "peso":1}],
                          [{"variable":"x"}], [{"variable":"x", "peso":"1"}],
                          [{"variable":["x"], "peso":1}], [{"variable":"x", "peso":True}],
                          [{"variable":"x", "peso":1},{"variable":"y"}]):
            with self.subTest(variables=variables):
                self.alert(self.prediction(variables=variables))
                self.assertEqual(self.get(), [])

    def test_acepta_pesos_negativos_y_cero(self):
        self.alert(self.prediction(variables=[{"variable":"x", "peso":0},{"variable":"y", "peso":-1}]))
        self.assertEqual(len(self.get()), 1)

    def test_pagina_despues_de_filtrar(self):
        first = self.alert(self.prediction(0),offset=1)
        second = self.alert(self.prediction(1),offset=2)
        self.alert(self.prediction(2,age=22),offset=3)
        self.assertEqual([r["id"] for r in self.get(limite=1)], [second.id])
        self.assertEqual([r["id"] for r in self.get(limite=1,desplazamiento=1)], [first.id])

    def test_false_y_ausencia_del_parametro_conservan_resultados(self):
        self.alert(self.prediction(age=22))
        self.alert(self.prediction())
        self.assertEqual(self.get(False), self.get(None))
        self.assertEqual(len(self.get(False)), 2)

    def test_fecha_emision_filtra_sin_reactivar_una_alerta_anterior(self):
        self.alert(self.prediction(age=1),offset=-86400)
        self.alert(self.prediction())
        self.assertEqual(self.get(hasta=(self.now.date()-timedelta(days=1)).isoformat()), [])

    def test_sin_token_401(self):
        self.assertEqual(self.client.get("/alertas?solo_vigentes=true").status_code,401)

    def test_permisos_de_todos_los_roles_conservados(self):
        for role in ("admin","sedes","coordinador_municipal","autoridad","epidemiologo"):
            with self.subTest(role=role):
                self.assertEqual(self.client.get("/alertas?solo_vigentes=true",headers=self.headers(role)).status_code,200)

    def test_parametro_invalido_422(self):
        r=self.client.get("/alertas?solo_vigentes=incorrecto",headers=self.headers())
        self.assertEqual(r.status_code,422)


if __name__ == "__main__":
    unittest.main()
