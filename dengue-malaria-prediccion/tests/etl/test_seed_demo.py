"""Verificacion de TASK-038: 'base vacia -> un comando -> GET /zonas/riesgo
devuelve zonas con prediccion'."""

import pytest
from sqlalchemy import func, select

from app.etl.seed_demo import sembrar_demo
from app.models import Alerta, BroteConfirmado, Modelo, Prediccion, Usuario

CLAVE_DEMO = "ClaveDeDemo-2026"
PILOTO = {"GUAYARAMERIN", "IXIAMAS", "PALOS BLANCOS", "SAN BUENAVENTURA"}


def _contar(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


@pytest.fixture()
def demo(db_session):
    return sembrar_demo(password=CLAVE_DEMO, db=db_session)


def test_registra_el_modelo_y_persiste_predicciones_de_la_zona_piloto(db_session, demo):
    assert demo["modelo_creado"] is True
    modelo = db_session.get(Modelo, demo["modelo_id"])
    assert modelo.nombre == "xgboost_baseline_dengue_t3"
    assert modelo.metricas_entrenamiento["tarea"] == "TASK-012"

    predicciones = db_session.execute(select(Prediccion)).scalars().all()
    assert len(predicciones) == demo["predicciones_insertadas"] > 0
    municipios = {p.municipio.nombre for p in predicciones}
    assert municipios <= PILOTO and municipios
    for p in predicciones:
        assert p.enfermedad.nombre == "dengue"
        assert p.nivel_riesgo in {"bajo", "medio", "alto"}
        assert 0 <= float(p.probabilidad_pct) <= 100
        assert len(p.variables_explicativas) >= 1  # REQ-004/REQ-005


def test_ingiere_los_casos_reales_del_boletin(db_session, demo):
    from app.models import CasoEpidemiologico

    casos = demo["casos"]
    assert casos["dengue_semanal"]["insertados"] == 4 * 13  # zona piloto x SE1-13
    assert casos["malaria_acumulada"]["insertados"] == 3     # solo 3 con malaria (ADR-005)
    assert _contar(db_session, CasoEpidemiologico) == 52 + 3


def test_sin_los_csv_procesados_omite_los_casos_y_sigue(db_session, tmp_path):
    resultado = sembrar_demo(password=CLAVE_DEMO, procesados=tmp_path, db=db_session)

    assert "omitida" in resultado["casos"]
    assert resultado["predicciones_insertadas"] > 0


def test_crea_los_cinco_usuarios_demo(db_session, demo):
    assert len(demo["usuarios"]) == 5
    assert _contar(db_session, Usuario) == 5


def test_no_inventa_malaria_brotes_ni_alertas(db_session, demo):
    enfermedades = {p.enfermedad.nombre for p in db_session.execute(select(Prediccion)).scalars()}
    assert enfermedades == {"dengue"}
    assert _contar(db_session, BroteConfirmado) == 0
    assert _contar(db_session, Alerta) == 0


def test_ejecutar_dos_veces_no_duplica_predicciones(db_session, demo):
    antes = _contar(db_session, Prediccion)

    segundo = sembrar_demo(password=CLAVE_DEMO, db=db_session)

    assert segundo["modelo_creado"] is False and segundo["modelo_id"] == demo["modelo_id"]
    assert segundo["predicciones_insertadas"] == 0
    assert "--forzar" in segundo["motivo_sin_predicciones"]
    assert _contar(db_session, Prediccion) == antes
    assert _contar(db_session, Modelo) == 1


def test_forzar_agrega_una_nueva_tanda_inmutable(db_session, demo):
    antes = _contar(db_session, Prediccion)

    tercero = sembrar_demo(password=CLAVE_DEMO, forzar=True, db=db_session)

    assert tercero["predicciones_insertadas"] == demo["predicciones_insertadas"]
    assert _contar(db_session, Prediccion) == antes + tercero["predicciones_insertadas"]


def test_la_api_devuelve_zonas_con_prediccion_tras_el_demo(client, demo):
    # Con un usuario demo real: login por la API, como en la demostracion.
    token = client.post(
        "/auth/login", data={"username": "autoridad@demo.local", "password": CLAVE_DEMO}
    ).json()["access_token"]

    cuerpo = client.get("/zonas/riesgo", headers={"Authorization": f"Bearer {token}"}).json()

    assert {z["municipio"] for z in cuerpo} <= PILOTO and cuerpo
    assert all(z["enfermedad"] == "dengue" for z in cuerpo)


def test_exige_una_clave_de_demo(db_session, monkeypatch):
    monkeypatch.delenv("SEED_DEMO_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="SEED_DEMO_PASSWORD"):
        sembrar_demo(db=db_session)
