"""Prueba extremo a extremo del backend (TASK-039 / NFR-010).

Recorre el mismo camino que la demostracion, con los datos REALES del repo:

  boletin (CSV oficial) -> ingesta -> base de datos -> modelo (TASK-014) ->
  predicciones persistidas -> login -> API -> respuesta distinta segun el rol.

No usa predicciones ni usuarios fabricados a mano: los crea el pipeline y el
seed de demostracion (TASK-038)."""

from pathlib import Path

import pytest

from app.etl.seed_demo import sembrar_demo

PROCESADOS = Path(__file__).resolve().parents[3] / "data" / "processed"
DENGUE_SEMANAL = PROCESADOS / "dengue_municipal_semanal.csv"
MALARIA = PROCESADOS / "malaria_municipal_validado.csv"
CLAVE = "ClaveDeDemo-2026"
PILOTO = {"GUAYARAMERIN", "IXIAMAS", "PALOS BLANCOS", "SAN BUENAVENTURA"}

pytestmark = pytest.mark.skipif(
    not (DENGUE_SEMANAL.exists() and MALARIA.exists()),
    reason="faltan los datos procesados del pipeline (data/processed)",
)


@pytest.fixture()
def sistema(client, db_session):
    """Base con casos reales ingeridos, modelo registrado y predicciones."""
    sembrar_demo(password=CLAVE, db=db_session)
    return client


def _entrar(client, email):
    respuesta = client.post("/auth/login", data={"username": email, "password": CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def test_flujo_completo_desde_el_boletin_hasta_la_respuesta_por_rol(sistema):
    client = sistema
    autoridad = _entrar(client, "autoridad@demo.local")
    epidemiologo = _entrar(client, "epidemiologo@demo.local")

    # 1. Mapa de riesgo: zonas de la zona piloto con prediccion del modelo.
    zonas = client.get("/zonas/riesgo", headers=autoridad).json()
    assert {z["municipio"] for z in zonas} == PILOTO
    assert all(z["enfermedad"] == "dengue" and z["geometria"]["type"] == "MultiPolygon" for z in zonas)
    zona = zonas[0]  # la de mayor riesgo

    # 2. Detalle de la zona: la autoridad ve el resumen; el epidemiologo, el
    #    detalle tecnico con las variables que explican la prediccion (SHAP).
    resumida = client.get(f"/zonas/{zona['municipio_id']}/prediccion", headers=autoridad).json()
    completa = client.get(f"/zonas/{zona['municipio_id']}/prediccion", headers=epidemiologo).json()
    assert resumida["vista"] == "resumida" and completa["vista"] == "completa"
    assert "variables_explicativas" not in resumida["predicciones"][0]
    variables = completa["predicciones"][0]["variables_explicativas"]
    assert len(variables) >= 3  # REQ-004
    assert all({"variable", "peso"} <= set(v) for v in variables)
    assert completa["predicciones"][0]["probabilidad_pct"] == resumida["predicciones"][0]["probabilidad_pct"]

    # 3. Casos observados: dengue semanal y malaria acumulada, tal como los
    #    entrega la fuente (ADR-005); la malaria no tiene prediccion.
    casos = {(c["municipio"], c["enfermedad"]): c
             for c in client.get("/casos/resumen", headers=autoridad).json()}
    assert casos[("GUAYARAMERIN", "dengue")]["granularidad"] == "semanal"
    assert casos[("GUAYARAMERIN", "malaria")]["granularidad"] == "acumulado"
    assert casos[("GUAYARAMERIN", "malaria")]["total_casos"] == 293  # boletin N.o 13
    assert {z["enfermedad"] for z in zonas} == {"dengue"}

    # 4. Control de acceso: el historial es solo para tecnicos.
    historial = f"/zonas/{zona['municipio_id']}/historial"
    assert client.get(historial, headers=autoridad).status_code == 403
    assert client.get(historial, headers=epidemiologo).status_code == 200


def test_el_admin_baja_el_umbral_y_la_siguiente_evaluacion_emite_alertas(sistema, db_session):
    """REQ-010 de punta a punta: el cambio de umbral rige en la siguiente
    evaluacion, sin redeploy, y las alertas llevan su justificacion (REQ-005)."""
    from app.ml.evaluacion_alertas import evaluar_alertas_pendientes

    client = sistema
    admin = _entrar(client, "admin@demo.local")
    autoridad = _entrar(client, "autoridad@demo.local")
    zonas = client.get("/zonas/riesgo", headers=autoridad).json()
    dengue_id = zonas[0]["enfermedad_id"]

    # Con el umbral por defecto (70 %) ninguna prediccion (15 a 44 %) alerta.
    assert client.get("/alertas", headers=autoridad).json() == []

    respuesta = client.post(
        "/admin/umbrales", headers=admin,
        json={"enfermedad_id": dengue_id, "umbral_probabilidad_pct": 40},
    )
    assert respuesta.status_code == 201

    resumen = evaluar_alertas_pendientes(db_session)

    alertas = client.get("/alertas", headers=autoridad).json()
    sobre_umbral = [z for z in zonas if z["probabilidad_pct"] >= 40]
    assert resumen["total_creadas"] == len(alertas) == len(sobre_umbral) > 0
    for alerta in alertas:
        assert alerta["umbral_aplicado"] == 40
        assert "supera el umbral configurado (40.0%)" in alerta["justificacion"]
        assert len(alerta["variables_explicativas"]) >= 1
    # Una zona bajo el umbral sigue sin alerta.
    assert {a["municipio_id"] for a in alertas} == {z["municipio_id"] for z in sobre_umbral}


def test_priorizacion_de_campanas_y_recursos_segun_el_rol(sistema):
    """TASK-024/025 con las predicciones reales del pipeline: SEDES ve todos los
    municipios; la coordinacion solo el suyo; el admin no ve campanas."""
    client = sistema
    sedes = _entrar(client, "sedes@demo.local")
    coordinador = _entrar(client, "coordinador@demo.local")   # asignado a Guayaramerin
    admin = _entrar(client, "admin@demo.local")

    ranking = client.get("/campanas/priorizacion", headers=sedes).json()
    assert {f["municipio"] for f in ranking} == PILOTO
    assert [f["posicion"] for f in ranking] == [1, 2, 3, 4]
    orden = {"alto": 0, "medio": 1, "bajo": 2}
    assert [orden[f["nivel_riesgo"]] for f in ranking] == sorted(orden[f["nivel_riesgo"]] for f in ranking)

    propio = client.get("/campanas/priorizacion", headers=coordinador).json()
    assert [f["municipio"] for f in propio] == ["GUAYARAMERIN"]

    assert client.get("/campanas/priorizacion", headers=admin).status_code == 403
    assert client.get("/campanas/priorizacion", headers=_entrar(client, "autoridad@demo.local")).status_code == 403

    mio = propio[0]["municipio_id"]
    recursos = client.get(f"/municipios/{mio}/recursos", headers=coordinador)
    assert recursos.status_code == 200
    cuerpo = recursos.json()
    assert cuerpo["nivel_atencion"] in {"PRIORITARIO", "PREVENTIVO", "RUTINARIO"}
    assert cuerpo["recomendaciones"] and "protocolos oficiales" in cuerpo["nota"]
    # La coordinacion no ve recursos de otro municipio; el admin si.
    otro = next(f["municipio_id"] for f in ranking if f["municipio_id"] != mio)
    assert client.get(f"/municipios/{otro}/recursos", headers=coordinador).status_code == 403
    assert client.get(f"/municipios/{otro}/recursos", headers=admin).status_code == 200


def test_sin_sesion_no_se_ve_nada(sistema):
    for ruta in ("/zonas/riesgo", "/casos/resumen", "/alertas", "/campanas/priorizacion"):
        assert sistema.get(ruta).status_code == 401


def test_credenciales_invalidas_no_dan_acceso(sistema):
    respuesta = sistema.post(
        "/auth/login", data={"username": "autoridad@demo.local", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401
    assert "access_token" not in respuesta.text


def test_la_base_caida_se_ve_como_servicio_no_disponible(sistema):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import get_db
    from app.main import app

    motor = create_engine("postgresql://u:p@127.0.0.1:1/x", connect_args={"connect_timeout": 1})
    sesion = sessionmaker(bind=motor)()
    token = _entrar(sistema, "admin@demo.local")  # antes de "apagar" la base
    app.dependency_overrides[get_db] = lambda: sesion
    try:
        assert sistema.get("/health/ready").status_code == 503
        assert sistema.get("/zonas/riesgo", headers=token).status_code == 503
        assert sistema.get("/health").status_code == 200  # la API sigue viva
    finally:
        sesion.close()
        motor.dispose()
