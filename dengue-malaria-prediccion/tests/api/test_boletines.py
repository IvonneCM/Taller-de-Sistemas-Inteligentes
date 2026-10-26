"""Carga de boletines en PDF: `POST /admin/boletines[/vista-previa]` (REQ-014, REQ-015).

Usa los boletines REALES del repo (data/boletines/)."""

from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.api.routes import boletines as ruta_boletines
from app.etl.fuentes import FUENTE_MINSALUD_SEMANAL, fuente_semanal
from app.models import CasoEpidemiologico
from tests.api.helpers import cabeceras

BOLETINES = Path(__file__).resolve().parents[3] / "data" / "boletines"
pytestmark = pytest.mark.skipif(
    not (BOLETINES / "SE13.pdf").exists(), reason="faltan los boletines en data/boletines"
)
URL = "/admin/boletines"
PILOTO = {"GUAYARAMERIN", "IXIAMAS", "PALOS BLANCOS", "SAN BUENAVENTURA"}


def _subir(client, nombre, *, previa=False, rol="epidemiologo"):
    contenido = (BOLETINES / nombre).read_bytes() if isinstance(nombre, str) else nombre
    return client.post(
        f"{URL}/vista-previa" if previa else URL,
        files={"archivo": ("boletin.pdf", contenido, "application/pdf")},
        headers=cabeceras(rol),
    )


def _filas(db):
    return db.execute(select(func.count(CasoEpidemiologico.id))).scalar_one()


def test_requiere_autenticacion(client):
    r = client.post(URL, files={"archivo": ("b.pdf", b"%PDF-", "application/pdf")})
    assert r.status_code == 401


@pytest.mark.parametrize("rol", ["autoridad", "sedes", "coordinador_municipal"])
def test_roles_sin_permiso_reciben_403(client, rol):
    assert _subir(client, "SE13.pdf", rol=rol).status_code == 403


def test_vista_previa_no_escribe(client, db_session):
    r = _subir(client, "SE13.pdf", previa=True)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["guardado"] is False
    assert (cuerpo["semana"], cuerpo["total_casos"], cuerpo["municipios_en_boletin"]) == (13, 341, 28)
    assert {m["municipio"] for m in cuerpo["municipios"]} == PILOTO
    assert len(cuerpo["fuera_de_catalogo"]) == 24
    assert cuerpo["filas_nuevas"] == 52
    assert _filas(db_session) == 0


@pytest.mark.parametrize("rol", ["epidemiologo", "admin"])
def test_guarda_la_serie_semanal_con_su_fuente(client, db_session, rol):
    r = _subir(client, "SE13.pdf", rol=rol)
    assert r.status_code == 200 and r.json()["guardado"] is True
    fuentes = db_session.execute(select(CasoEpidemiologico.fuente).distinct()).scalars().all()
    assert fuentes == [FUENTE_MINSALUD_SEMANAL]  # el mismo texto que usa la ingesta del pipeline
    assert _filas(db_session) == 52

    # Lo ven el resumen de casos y el panel como serie semanal (no como acumulado).
    casos = client.get("/casos/resumen", headers=cabeceras()).json()
    guaya = next(c for c in casos if c["municipio"] == "GUAYARAMERIN")
    assert (guaya["granularidad"], guaya["total_casos"]) == ("semanal", 9)
    panel = client.get("/panel/resumen", headers=cabeceras()).json()
    assert panel["dengue"]["total_casos"] == 51  # 4 municipios piloto del SE 13


def test_subir_dos_veces_no_duplica(client, db_session):
    _subir(client, "SE13.pdf")
    r = _subir(client, "SE13.pdf")
    assert r.status_code == 200
    assert {m["accion"] for m in r.json()["municipios"]} == {"omitido"}
    assert r.json()["filas_nuevas"] == r.json()["filas_actualizadas"] == 0
    assert _filas(db_session) == 52


def test_boletin_nuevo_corrige_al_anterior(client, db_session):
    _subir(client, "SE09.pdf")
    antes = _filas(db_session)
    r = _subir(client, "SE13.pdf").json()

    guaya = next(m for m in r["municipios"] if m["municipio"] == "GUAYARAMERIN")
    assert (guaya["accion"], guaya["boletin_anterior"], guaya["semanas_nuevas"]) == ("actualiza", 9, 4)
    assert r["filas_actualizadas"] == antes
    # Una sola serie por municipio: todas las filas quedan con la fuente del boletin 13.
    fuentes = db_session.execute(select(CasoEpidemiologico.fuente).distinct()).scalars().all()
    assert fuentes == [fuente_semanal(13)]
    assert _filas(db_session) == 52


def test_boletin_viejo_no_deshace_correcciones(client, db_session):
    _subir(client, "SE13.pdf")
    r = _subir(client, "SE09.pdf").json()
    assert {m["accion"] for m in r["municipios"]} == {"omitido"}
    assert {m["boletin_anterior"] for m in r["municipios"]} == {13}
    fuentes = db_session.execute(select(CasoEpidemiologico.fuente).distinct()).scalars().all()
    assert fuentes == [fuente_semanal(13)]


def test_boletin_sin_tabla_responde_400_con_motivo(client, db_session):
    r = _subir(client, "SE21.pdf")
    assert r.status_code == 400
    assert "no trae la tabla" in r.json()["detail"]
    assert _filas(db_session) == 0


def test_archivo_que_no_es_pdf_responde_400(client):
    r = _subir(client, b"municipio,casos\nX,1\n")
    assert r.status_code == 400 and r.json()["detail"] == "El archivo no es un PDF."


def test_archivo_demasiado_grande_responde_413(client, monkeypatch):
    monkeypatch.setattr(ruta_boletines, "MAX_BYTES", 1024)
    assert _subir(client, "SE13.pdf").status_code == 413
