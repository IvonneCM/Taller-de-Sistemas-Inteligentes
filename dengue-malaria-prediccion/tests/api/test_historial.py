"""Verificacion de TASK-021: 'test de integracion con datos de ejemplo
devuelve ambos conjuntos correlacionados por fecha' (REQ-008, NFR-002)."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.services.historial import VENTANA_CORRELACION_DIAS
from tests.api.helpers import cabeceras, crear_brote, crear_modelo, crear_prediccion

GEN_1 = datetime(2026, 2, 9, 12, 0, tzinfo=timezone.utc)   # estimada: 2026-03-06 (+25)
GEN_2 = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)   # estimada: 2026-03-27 (+25)


def _url(zona):
    return f"/zonas/{zona.id}/historial"


@pytest.mark.parametrize("rol", ["autoridad", "sedes", "coordinador_municipal"])
def test_roles_no_tecnicos_reciben_403(client, guayaramerin, rol):
    assert client.get(_url(guayaramerin), headers=cabeceras(rol)).status_code == 403


def test_requiere_autenticacion(client, guayaramerin):
    assert client.get(_url(guayaramerin)).status_code == 401


@pytest.mark.parametrize("rol", ["epidemiologo", "admin"])
def test_epidemiologo_y_admin_acceden(client, guayaramerin, rol):
    respuesta = client.get(_url(guayaramerin), headers=cabeceras(rol))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["municipio"] == "GUAYARAMERIN"
    assert cuerpo["predicciones"] == []
    assert cuerpo["brotes_confirmados"] == []
    assert cuerpo["ventana_correlacion_dias"] == VENTANA_CORRELACION_DIAS


def test_zona_inexistente_responde_404(client):
    assert client.get("/zonas/999999/historial", headers=cabeceras("admin")).status_code == 404


def test_devuelve_predicciones_y_brotes_correlacionados_por_fecha(
    client, db_session, dengue, modelo, guayaramerin
):
    p1 = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                          nivel="alto", probabilidad=85, generada=GEN_1)
    p2 = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                          nivel="medio", probabilidad=45, generada=GEN_2)
    # Brote 3 dias despues de lo estimado para p1; nada cerca de p2.
    brote = crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                        fecha=date(2026, 3, 9))

    cuerpo = client.get(_url(guayaramerin), headers=cabeceras("epidemiologo")).json()

    assert [p["prediccion_id"] for p in cuerpo["predicciones"]] == [p1.id, p2.id]  # cronologico
    acierto, sin_brote = cuerpo["predicciones"]
    assert acierto["brote_confirmado"] is True
    assert acierto["brote_confirmado_id"] == brote.id
    assert acierto["fecha_brote_confirmado"] == "2026-03-09"
    assert acierto["anticipacion_dias"] == 28  # 9-feb -> 9-mar
    assert sin_brote["brote_confirmado"] is False
    assert sin_brote["brote_confirmado_id"] is None
    assert sin_brote["fecha_brote_confirmado"] is None
    assert sin_brote["anticipacion_dias"] is None
    assert [b["id"] for b in cuerpo["brotes_confirmados"]] == [brote.id]
    assert cuerpo["brotes_confirmados"][0]["enfermedad"] == "dengue"
    assert cuerpo["brotes_confirmados"][0]["fuente"] == "boletin de ejemplo"


@pytest.mark.parametrize(
    "desfase, correlaciona",
    [(-VENTANA_CORRELACION_DIAS, True), (0, True), (VENTANA_CORRELACION_DIAS, True),
     (VENTANA_CORRELACION_DIAS + 1, False), (-VENTANA_CORRELACION_DIAS - 1, False)],
)
def test_ventana_de_correlacion_es_inclusiva(
    client, db_session, dengue, modelo, guayaramerin, desfase, correlaciona
):
    p = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                         generada=GEN_1)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                fecha=p.fecha_estimada_riesgo + timedelta(days=desfase))

    cuerpo = client.get(_url(guayaramerin), headers=cabeceras("admin")).json()

    assert cuerpo["predicciones"][0]["brote_confirmado"] is correlaciona


def test_con_varios_brotes_toma_el_mas_cercano_a_la_fecha_estimada(
    client, db_session, dengue, modelo, guayaramerin
):
    p = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                         generada=GEN_1)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                fecha=p.fecha_estimada_riesgo - timedelta(days=5))
    cercano = crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                          fecha=p.fecha_estimada_riesgo + timedelta(days=1))

    cuerpo = client.get(_url(guayaramerin), headers=cabeceras("admin")).json()

    assert cuerpo["predicciones"][0]["brote_confirmado_id"] == cercano.id


def test_ignora_brotes_de_otra_enfermedad_o_de_otra_zona(
    client, db_session, dengue, malaria, modelo, guayaramerin, ixiamas
):
    p = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                         generada=GEN_1)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=malaria,
                fecha=p.fecha_estimada_riesgo)
    crear_brote(db_session, municipio=ixiamas, enfermedad=dengue,
                fecha=p.fecha_estimada_riesgo)

    cuerpo = client.get(_url(guayaramerin), headers=cabeceras("admin")).json()

    assert cuerpo["predicciones"][0]["brote_confirmado"] is False
    # El brote de malaria de esta zona si aparece en la lista de brotes.
    assert [b["enfermedad"] for b in cuerpo["brotes_confirmados"]] == ["malaria"]


def test_filtra_por_rango_de_fechas_y_enfermedad(
    client, db_session, dengue, malaria, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     generada=GEN_1)
    p2 = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                          generada=GEN_2)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=malaria,
                     modelo=crear_modelo(db_session, malaria), generada=GEN_2)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 3, 9))
    brote_tardio = crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                               fecha=date(2026, 4, 1))

    cuerpo = client.get(
        f"{_url(guayaramerin)}?desde=2026-03-01&hasta=2026-03-31&enfermedad_id={dengue.id}",
        headers=cabeceras("admin"),
    ).json()

    assert [p["prediccion_id"] for p in cuerpo["predicciones"]] == [p2.id]
    assert [b["fecha_confirmacion"] for b in cuerpo["brotes_confirmados"]] == ["2026-03-09"]
    assert brote_tardio.id not in [b["id"] for b in cuerpo["brotes_confirmados"]]
    assert cuerpo["desde"] == "2026-03-01"
    assert cuerpo["hasta"] == "2026-03-31"


def test_la_correlacion_no_pierde_brotes_fuera_del_rango_pedido(
    client, db_session, dengue, modelo, guayaramerin
):
    # La prediccion cae en el rango; su brote (confirmado ~4 semanas despues)
    # cae fuera. Se correlaciona igual, aunque no aparezca en la lista.
    p = crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                         generada=GEN_2)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue,
                fecha=p.fecha_estimada_riesgo)

    cuerpo = client.get(
        f"{_url(guayaramerin)}?desde=2026-03-01&hasta=2026-03-10", headers=cabeceras("admin")
    ).json()

    assert cuerpo["predicciones"][0]["brote_confirmado"] is True
    assert cuerpo["brotes_confirmados"] == []


def test_rango_invertido_responde_422(client, guayaramerin):
    respuesta = client.get(
        f"{_url(guayaramerin)}?desde=2026-04-01&hasta=2026-03-01", headers=cabeceras("admin")
    )
    assert respuesta.status_code == 422


def test_fecha_invalida_responde_422(client, guayaramerin):
    assert client.get(
        f"{_url(guayaramerin)}?desde=ayer", headers=cabeceras("admin")
    ).status_code == 422


def test_enfermedad_inexistente_responde_404(client, guayaramerin):
    assert client.get(
        f"{_url(guayaramerin)}?enfermedad_id=9999", headers=cabeceras("admin")
    ).status_code == 404
