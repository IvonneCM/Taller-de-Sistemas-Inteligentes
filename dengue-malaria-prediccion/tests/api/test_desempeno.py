"""Verificacion de TASK-026: `GET /modelo/desempeno` con datos de ejemplo
(REQ-016; insumo de NFR-001 y NFR-002).

Los datos son ejemplos de prueba, no cifras epidemiologicas reales."""

from datetime import date, datetime, timezone

import pytest

from tests.api.helpers import cabeceras, crear_brote, crear_prediccion

GEN_1 = datetime(2026, 2, 9, 12, 0, tzinfo=timezone.utc)   # estimada: 2026-03-06
GEN_2 = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)   # estimada: 2026-03-27
GEN_3 = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)   # estimada: 2026-04-03

URL = "/modelo/desempeno"


@pytest.mark.parametrize("rol", ["autoridad", "sedes", "coordinador_municipal"])
def test_roles_no_tecnicos_reciben_403(client, rol):
    assert client.get(URL, headers=cabeceras(rol)).status_code == 403


def test_requiere_autenticacion(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("rol", ["epidemiologo", "admin"])
def test_epidemiologo_y_admin_acceden(client, rol):
    assert client.get(URL, headers=cabeceras(rol)).status_code == 200


def test_sin_predicciones_las_metricas_son_nulas_no_cero(client):
    cuerpo = client.get(URL, headers=cabeceras()).json()
    assert cuerpo["estado"] == "sin_predicciones"
    assert cuerpo["predicciones_evaluadas"] == 0
    for campo in ("precision_espacial_pct", "sensibilidad_pct",
                  "anticipacion_dias_media", "anticipacion_dias_mediana"):
        assert cuerpo[campo] is None
    assert cuerpo["objetivos"]["anticipacion_dias"] == 14
    assert "piloto" in cuerpo["nota"]


def test_sin_brotes_no_se_calcula_precision(client, db_session, dengue, modelo, guayaramerin):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)
    cuerpo = client.get(URL, headers=cabeceras()).json()
    assert cuerpo["estado"] == "sin_brotes_confirmados"
    assert cuerpo["predicciones_positivas"] == 1
    assert cuerpo["precision_espacial_pct"] is None   # sin brotes no se sabe si fue falsa alarma
    assert cuerpo["sensibilidad_pct"] is None
    assert cuerpo["anticipacion_dias_media"] is None


def test_calcula_precision_sensibilidad_y_anticipacion(
    client, db_session, dengue, modelo, guayaramerin, ixiamas
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)                       # acierto
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="medio", generada=GEN_2)                      # falsa alarma
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="bajo", generada=GEN_3)                       # no es positiva
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 3, 9))
    crear_brote(db_session, municipio=ixiamas, enfermedad=dengue, fecha=date(2026, 3, 10))  # sin prediccion

    cuerpo = client.get(URL, headers=cabeceras()).json()

    assert cuerpo["estado"] == "calculado"
    assert cuerpo["predicciones_evaluadas"] == 3
    assert cuerpo["predicciones_positivas"] == 2
    assert cuerpo["aciertos"] == 1
    assert cuerpo["falsas_alarmas"] == 1
    assert cuerpo["brotes_confirmados"] == 2
    assert cuerpo["brotes_detectados"] == 1
    assert cuerpo["precision_espacial_pct"] == 50.0
    assert cuerpo["sensibilidad_pct"] == 50.0
    assert cuerpo["anticipacion_dias_media"] == 28.0       # 9-feb -> 9-mar
    assert cuerpo["anticipacion_dias_mediana"] == 28.0
    assert cuerpo["aciertos_con_anticipacion_minima"] == 1


def test_nivel_minimo_alto_deja_fuera_las_predicciones_medias(
    client, db_session, dengue, modelo, guayaramerin
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="medio", generada=GEN_2)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 3, 9))

    cuerpo = client.get(URL, params={"nivel_minimo": "alto"}, headers=cabeceras()).json()
    assert cuerpo["predicciones_positivas"] == 1
    assert cuerpo["precision_espacial_pct"] == 100.0


def test_un_brote_de_otra_enfermedad_o_zona_no_cuenta(
    client, db_session, dengue, malaria, modelo, guayaramerin, ixiamas
):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=malaria, fecha=date(2026, 3, 9))
    crear_brote(db_session, municipio=ixiamas, enfermedad=dengue, fecha=date(2026, 3, 9))

    cuerpo = client.get(URL, headers=cabeceras()).json()
    assert cuerpo["aciertos"] == 0
    assert cuerpo["brotes_detectados"] == 0
    assert cuerpo["precision_espacial_pct"] == 0.0


def test_filtra_por_enfermedad(client, db_session, dengue, malaria, modelo, guayaramerin):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 3, 9))

    con_dengue = client.get(URL, params={"enfermedad_id": dengue.id}, headers=cabeceras()).json()
    con_malaria = client.get(URL, params={"enfermedad_id": malaria.id}, headers=cabeceras()).json()
    assert con_dengue["aciertos"] == 1
    assert con_malaria["estado"] == "sin_predicciones"


def test_filtra_por_periodo(client, db_session, dengue, modelo, guayaramerin):
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)   # estimada 2026-03-06
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_3)   # estimada 2026-04-03
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 3, 9))

    cuerpo = client.get(URL, params={"desde": "2026-03-01", "hasta": "2026-03-15"},
                        headers=cabeceras()).json()
    assert cuerpo["predicciones_evaluadas"] == 1
    assert cuerpo["aciertos"] == 1
    assert cuerpo["precision_espacial_pct"] == 100.0


def test_anticipacion_en_el_limite_de_la_ventana_iguala_el_objetivo(
    client, db_session, dengue, modelo, guayaramerin
):
    # Horizonte minimo (21 dias) y brote 7 dias antes de lo estimado: 14 dias de
    # anticipacion. Por construccion (horizonte >= 21, ventana +-7) un acierto
    # nunca anticipa menos que el objetivo de NFR-002.
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1, dias=21)          # estimada 2026-03-02
    crear_brote(db_session, municipio=guayaramerin, enfermedad=dengue, fecha=date(2026, 2, 23))

    cuerpo = client.get(URL, headers=cabeceras()).json()
    assert cuerpo["aciertos"] == 1
    assert cuerpo["anticipacion_dias_media"] == 14.0
    assert cuerpo["aciertos_con_anticipacion_minima"] == 1


def test_rango_invertido_responde_422(client):
    r = client.get(URL, params={"desde": "2026-04-01", "hasta": "2026-03-01"}, headers=cabeceras())
    assert r.status_code == 422


def test_enfermedad_inexistente_responde_404(client):
    assert client.get(URL, params={"enfermedad_id": 999999}, headers=cabeceras()).status_code == 404


def test_nivel_minimo_invalido_responde_422(client):
    assert client.get(URL, params={"nivel_minimo": "extremo"}, headers=cabeceras()).status_code == 422


def test_brotes_simulados_de_la_vista(db_session, dengue, malaria, modelo, guayaramerin):
    """TASK-034: la vista brotes_simulados suma las fuentes de un mismo dia, ignora
    los dias sin casos y respeta el filtro por enfermedad."""
    from app.models import CasoEpidemiologico
    from app.services.desempeno import calcular_desempeno

    def caso(enfermedad, fecha, n, fuente):
        db_session.add(CasoEpidemiologico(municipio_id=guayaramerin.id, enfermedad_id=enfermedad.id,
                                          fecha_reporte=fecha, casos_confirmados=n, fuente=fuente))

    caso(dengue, date(2026, 3, 9), 2, "boletin A")
    caso(dengue, date(2026, 3, 9), 1, "boletin B")      # mismo dia, otra fuente: un solo brote
    caso(dengue, date(2026, 3, 16), 0, "boletin A")     # sin casos: no cuenta
    caso(malaria, date(2026, 3, 9), 5, "boletin A")     # otra enfermedad: filtrada
    db_session.flush()
    crear_prediccion(db_session, municipio=guayaramerin, enfermedad=dengue, modelo=modelo,
                     nivel="alto", generada=GEN_1)

    r = calcular_desempeno(db_session, enfermedad_id=dengue.id, desde=date(2026, 3, 1),
                           usar_brotes_simulados=True)

    assert r["brotes_confirmados"] == 1
    assert r["brotes_detectados"] == 1
    assert r["aciertos"] == 1
    # Por defecto sigue usando brotes_confirmados (vacia en esta prueba).
    assert calcular_desempeno(db_session, enfermedad_id=dengue.id)["brotes_confirmados"] == 0
