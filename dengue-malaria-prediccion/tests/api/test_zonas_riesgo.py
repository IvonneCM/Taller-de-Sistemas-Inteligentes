"""Verificacion de TASK-019: 'test de integracion devuelve lista con
nivel_riesgo y coordenadas/geometria para cada municipio' (REQ-001,
REQ-006)."""

from datetime import datetime, timedelta, timezone

from tests.api.helpers import cabeceras, crear_modelo, crear_prediccion

AHORA = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)


def test_requiere_autenticacion(client):
    assert client.get("/zonas/riesgo").status_code == 401


def test_sin_predicciones_devuelve_lista_vacia(client):
    respuesta = client.get("/zonas/riesgo", headers=cabeceras("autoridad"))
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_devuelve_nivel_de_riesgo_y_geometria_por_municipio(
    client, db_session, catalogo, dengue, modelo, guayaramerin, ixiamas
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", probabilidad=82.5, generada=AHORA)
    crear_prediccion(db_session, municipio=ixiamas, enfermedad=dengue, modelo=modelo,
                     nivel="bajo", probabilidad=12, generada=AHORA)

    respuesta = client.get("/zonas/riesgo", headers=cabeceras("autoridad"))

    assert respuesta.status_code == 200
    zonas = {z["municipio"]: z for z in respuesta.json()}
    assert set(zonas) == {"GUAYARAMERIN", "IXIAMAS"}
    gua = zonas["GUAYARAMERIN"]
    assert gua["nivel_riesgo"] == "alto"
    assert gua["probabilidad_pct"] == 82.5
    assert gua["nivel_confianza"] == "medio"
    assert gua["enfermedad"] == "dengue"
    assert gua["departamento"] == "Beni"
    assert gua["municipio_id"] == guayaramerin.id
    # Geometria GeoJSON valida y centroide dentro de ella.
    assert gua["geometria"]["type"] == "MultiPolygon"
    anillo = gua["geometria"]["coordinates"][0][0]
    assert anillo[0] == anillo[-1]
    lons = [p[0] for p in anillo]
    lats = [p[1] for p in anillo]
    assert min(lons) < gua["centroide"]["lon"] < max(lons)
    assert min(lats) < gua["centroide"]["lat"] < max(lats)
    assert abs(gua["centroide"]["lat"] - (-10.83391)) < 0.01
    assert abs(gua["centroide"]["lon"] - (-65.34004)) < 0.01


def test_usa_la_prediccion_mas_reciente_de_cada_zona_y_enfermedad(
    client, db_session, dengue, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="bajo", probabilidad=10, generada=AHORA - timedelta(days=14))
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", probabilidad=90, generada=AHORA)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="medio", probabilidad=50, generada=AHORA - timedelta(days=7))

    zonas = client.get("/zonas/riesgo", headers=cabeceras("sedes")).json()

    assert len(zonas) == 1
    assert zonas[0]["nivel_riesgo"] == "alto"
    assert zonas[0]["probabilidad_pct"] == 90


def test_empate_de_fecha_desempata_por_id_mas_reciente(
    client, db_session, dengue, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="bajo", probabilidad=10, generada=AHORA)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="medio", probabilidad=55, generada=AHORA)

    zonas = client.get("/zonas/riesgo", headers=cabeceras("sedes")).json()

    assert [z["probabilidad_pct"] for z in zonas] == [55]


def test_una_fila_por_zona_y_enfermedad_y_filtro_por_enfermedad(
    client, db_session, dengue, malaria, modelo, guayaramerin
):
    modelo_malaria = crear_modelo(db_session, malaria)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", probabilidad=80, generada=AHORA)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=malaria,
                     modelo=modelo_malaria, nivel="bajo", probabilidad=5, generada=AHORA)

    todas = client.get("/zonas/riesgo", headers=cabeceras("sedes")).json()
    solo_malaria = client.get(
        f"/zonas/riesgo?enfermedad_id={malaria.id}", headers=cabeceras("sedes")
    ).json()

    assert {z["enfermedad"] for z in todas} == {"dengue", "malaria"}
    assert [z["enfermedad"] for z in solo_malaria] == ["malaria"]
    assert solo_malaria[0]["nivel_riesgo"] == "bajo"


def test_enfermedad_inexistente_responde_404(client):
    respuesta = client.get("/zonas/riesgo?enfermedad_id=9999", headers=cabeceras("sedes"))
    assert respuesta.status_code == 404


def test_enfermedad_id_no_numerico_responde_422(client):
    respuesta = client.get("/zonas/riesgo?enfermedad_id=abc", headers=cabeceras("sedes"))
    assert respuesta.status_code == 422


def test_ordena_primero_el_mayor_riesgo_y_probabilidad(
    client, db_session, catalogo, dengue, modelo
):
    municipios = catalogo["municipios"]
    datos = [
        ("GUAYARAMERIN", "bajo", 5),
        ("IXIAMAS", "alto", 75),
        ("PALOS BLANCOS", "alto", 91),
        ("SAN BUENAVENTURA", "medio", 55),
    ]
    for nombre, nivel, prob in datos:
        crear_prediccion(db_session, municipio=municipios[nombre], enfermedad=dengue,
                         modelo=modelo, nivel=nivel, probabilidad=prob, generada=AHORA)

    zonas = client.get("/zonas/riesgo", headers=cabeceras("autoridad")).json()

    assert [z["municipio"] for z in zonas] == [
        "PALOS BLANCOS", "IXIAMAS", "SAN BUENAVENTURA", "GUAYARAMERIN",
    ]


def test_no_expone_variables_explicativas_ni_modelo_en_el_mapa(
    client, db_session, dengue, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     generada=AHORA)
    zona = client.get("/zonas/riesgo", headers=cabeceras("autoridad")).json()[0]
    assert "variables_explicativas" not in zona
    assert "modelo_id" not in zona
