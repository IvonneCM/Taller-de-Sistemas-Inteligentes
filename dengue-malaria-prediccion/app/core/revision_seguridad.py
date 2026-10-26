"""Revision de seguridad y cumplimiento verificable (TASK-035).

    python -m app.core.revision_seguridad            # base, codigo y repositorio
    python -m app.core.revision_seguridad --url https://mi-app.example.com

Cada control devuelve OK, FALLA, AVISO o NO VERIFICADO y el comando sale con
codigo 1 si hay alguna FALLA. Es la evidencia tecnica del checklist de
`docs/revision_seguridad.md`; NO sustituye la firma del equipo ni una auditoria.

Lo que NO puede comprobar por si solo queda como NO VERIFICADO (por ejemplo,
HTTPS mientras no exista un despliegue): nunca se da por bueno lo que no se vio.
"""

from __future__ import annotations

import argparse
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import text

OK, FALLA, AVISO, NO_VERIFICADO = "OK", "FALLA", "AVISO", "NO VERIFICADO"

RAIZ_APP = Path(__file__).resolve().parents[1]
RAIZ_BACKEND = RAIZ_APP.parent


@dataclass(frozen=True)
class Resultado:
    control: str
    requisito: str
    estado: str
    detalle: str


# ---------------------------------------------------------------- base de datos

# Nombres de columna que delatarian datos personales de pacientes (REQ-020).
_PII = re.compile(
    r"paciente|apellido|nombre_completo|(^|_)(ci|dni|cedula|documento|telefono|celular|"
    r"direccion|domicilio|nacimiento|historia_clinica|sexo|genero|edad)($|_)",
    re.IGNORECASE,
)
# Datos del PERSONAL que opera el sistema, no de pacientes.
_PERMITIDAS = {("usuarios", "email")}
_TABLAS_DE_SISTEMA = ("spatial_ref_sys", "alembic_version", "geography_columns", "geometry_columns")


def sin_datos_personales(conexion) -> Resultado:
    filas = conexion.execute(text(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name <> ALL(:sistema)"
    ), {"sistema": list(_TABLAS_DE_SISTEMA)}).all()
    sospechosas = [f"{t}.{c}" for t, c in filas if _PII.search(c) and (t, c) not in _PERMITIDAS]
    if sospechosas:
        return Resultado("Sin datos personales de pacientes", "REQ-020", FALLA,
                         "columnas sospechosas: " + ", ".join(sorted(sospechosas)))
    return Resultado("Sin datos personales de pacientes", "REQ-020", OK,
                     f"{len(filas)} columnas revisadas; solo el correo del personal (usuarios.email)")


def alertas_con_justificacion(conexion) -> Resultado:
    vacias, sin_variables, total = conexion.execute(text(
        "SELECT count(*) FILTER (WHERE length(btrim(a.justificacion)) = 0), "
        "count(*) FILTER (WHERE jsonb_typeof(p.variables_explicativas) <> 'array' "
        "                 OR jsonb_array_length(CASE WHEN jsonb_typeof(p.variables_explicativas) = 'array' "
        "                      THEN p.variables_explicativas ELSE '[]'::jsonb END) = 0), "
        "count(*) FROM alertas a JOIN predicciones p ON p.id = a.prediccion_id"
    )).one()
    if vacias or sin_variables:
        return Resultado("Ninguna alerta sin justificacion", "REQ-005", FALLA,
                         f"{vacias} sin justificacion y {sin_variables} sin variables explicativas de {total}")
    return Resultado("Ninguna alerta sin justificacion", "REQ-005", OK,
                     f"{total} alertas revisadas; todas con justificacion y variables explicativas")


def contrasenas_con_hash(conexion) -> Resultado:
    malas, total = conexion.execute(text(
        "SELECT count(*) FILTER (WHERE password_hash !~ '^\\$2[abxy]\\$[0-9]{2}\\$.{53}$'), count(*) FROM usuarios"
    )).one()
    if malas:
        return Resultado("Contrasenas almacenadas con hash bcrypt", "NFR-005", FALLA,
                         f"{malas} de {total} usuarios sin un hash bcrypt valido")
    return Resultado("Contrasenas almacenadas con hash bcrypt", "NFR-005", OK,
                     f"{total} usuarios; todos con hash bcrypt")


# ------------------------------------------------------------------- codigo

_ACTUALIZA_PREDICCION = re.compile(
    r"update\s*\(\s*Prediccion\b|UPDATE\s+predicciones\b|query\s*\(\s*Prediccion\s*\)\s*\.\s*(update|delete)\b"
    r"|delete\s*\(\s*Prediccion\b|DELETE\s+FROM\s+predicciones\b",
    re.IGNORECASE,
)


def predicciones_inmutables(archivos: dict[str, str] | None = None) -> Resultado:
    """NFR-009: el codigo de la aplicacion solo inserta en `predicciones`."""
    if archivos is None:
        archivos = {str(p.relative_to(RAIZ_BACKEND)): p.read_text(encoding="utf-8")
                    for p in RAIZ_APP.rglob("*.py")}
    hallazgos = [ruta for ruta, contenido in archivos.items() if _ACTUALIZA_PREDICCION.search(contenido)]
    if hallazgos:
        return Resultado("Predicciones inmutables en el codigo", "NFR-009", FALLA,
                         "modifican o borran predicciones: " + ", ".join(sorted(hallazgos)))
    return Resultado("Predicciones inmutables en el codigo", "NFR-009", OK,
                     f"{len(archivos)} archivos revisados; ninguno actualiza ni borra predicciones "
                     "(la inmutabilidad es de aplicacion, no de la base)")


def configuracion_segura(entorno: dict | None = None) -> Resultado:
    e = os.environ if entorno is None else entorno
    clave = e.get("SECRET_KEY", "")
    produccion = e.get("ENVIRONMENT", "development").lower() == "production"
    debil = len(clave) < 32 or "cambiar" in clave.lower()
    if debil and produccion:
        return Resultado("SECRET_KEY robusta", "NFR-005", FALLA, "clave debil o de ejemplo con ENVIRONMENT=production")
    if debil:
        return Resultado("SECRET_KEY robusta", "NFR-005", AVISO,
                         "clave corta o de ejemplo (aceptable solo en desarrollo; en produccion la aplicacion no arranca)")
    if e.get("ALGORITHM", "HS256").upper() != "HS256":
        return Resultado("SECRET_KEY robusta", "NFR-005", FALLA, "ALGORITHM distinto de HS256")
    return Resultado("SECRET_KEY robusta", "NFR-005", OK, "clave de al menos 32 caracteres y HS256")


# --------------------------------------------------------------- repositorio

_PLACEHOLDERS = ("cambiar", "prueba", "test", "ejemplo", "local", "desarrollo", "devlocal", "ci-solo", "tu-", "xxx", "elegir")
_URL_CON_CLAVE = re.compile(r"postgres(?:ql)?://[^:\s/@]+:([^@\s]+)@", re.IGNORECASE)
_CLAVE_LARGA = re.compile(r"""SECRET_KEY\s*[:=]\s*['"]?([A-Za-z0-9+/_\-]{32,})""")
_CLAVE_PRIVADA = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_CLAVES_DE_DOCUMENTACION = {"postgres", "test", "x", "y", "u", "p", "pass", "password", "clave", "contrasena"}


def _es_ficticia(valor: str) -> bool:
    v = valor.lower().strip("'\"")
    return (v in _CLAVES_DE_DOCUMENTACION or v.startswith(("$", "{", "<", "%"))
            or any(p in v for p in _PLACEHOLDERS))


def secretos_en_el_repositorio(archivos: dict[str, str]) -> Resultado:
    """Busca secretos reales en los archivos versionados (heuristica, no auditoria)."""
    hallazgos: list[str] = []
    for ruta, contenido in archivos.items():
        nombre = ruta.rsplit("/", 1)[-1]
        if nombre == ".env" or (nombre.startswith(".env.") and nombre != ".env.example"):
            hallazgos.append(f"{ruta}: archivo de entorno versionado")
        if _CLAVE_PRIVADA.search(contenido):
            hallazgos.append(f"{ruta}: clave privada")
        if _AWS.search(contenido):
            hallazgos.append(f"{ruta}: clave de acceso de AWS")
        for clave in _URL_CON_CLAVE.findall(contenido):
            if not _es_ficticia(clave):
                hallazgos.append(f"{ruta}: URL de base de datos con una clave que no parece de ejemplo")
        for clave in _CLAVE_LARGA.findall(contenido):
            if not _es_ficticia(clave):
                hallazgos.append(f"{ruta}: SECRET_KEY con valor real")
    if hallazgos:
        return Resultado("Sin secretos en el repositorio", "NFR-005", FALLA, "; ".join(sorted(set(hallazgos))))
    return Resultado("Sin secretos en el repositorio", "NFR-005", OK,
                     f"{len(archivos)} archivos versionados revisados (busqueda heuristica)")


def archivos_versionados(raiz: Path | None = None) -> dict[str, str] | None:
    """Contenido de los archivos de texto que git versiona; None si no hay git."""
    raiz = raiz or RAIZ_BACKEND.parent
    try:
        salida = subprocess.run(["git", "ls-files", "-z"], cwd=raiz, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    archivos: dict[str, str] = {}
    for ruta in salida.decode("utf-8", "replace").split("\0"):
        archivo = raiz / ruta
        if not ruta or not archivo.is_file() or archivo.stat().st_size > 1_000_000:
            continue
        try:
            archivos[ruta] = archivo.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binario
    return archivos


# --------------------------------------------------------------------- HTTPS

def https_en_despliegue(url: str | None) -> Resultado:
    nombre = "HTTPS en el despliegue"
    if not url:
        return Resultado(nombre, "NFR-005", NO_VERIFICADO,
                         "no hay despliegue que revisar (TASK-004); ejecutar con --url https://...")
    partes = urlparse(url)
    if partes.scheme != "https":
        return Resultado(nombre, "NFR-005", FALLA, f"la URL usa {partes.scheme or 'ningun esquema'}, no https")
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=10,
                                    context=ssl.create_default_context()) as respuesta:
            estado, cabeceras = respuesta.status, respuesta.headers
    except (urllib.error.URLError, ssl.SSLError, OSError) as error:
        return Resultado(nombre, "NFR-005", FALLA, f"no responde por https con un certificado valido: {error}")
    if estado != 200:
        return Resultado(nombre, "NFR-005", FALLA, f"/health respondio {estado}")
    if "strict-transport-security" not in {k.lower() for k in cabeceras.keys()}:
        return Resultado(nombre, "NFR-005", AVISO, "https y certificado validos, pero sin Strict-Transport-Security")
    return Resultado(nombre, "NFR-005", OK, "https con certificado valido y Strict-Transport-Security")


# ----------------------------------------------------------------------- CLI

def ejecutar(conexion, *, url: str | None = None) -> list[Resultado]:
    archivos = archivos_versionados()
    return [
        sin_datos_personales(conexion),
        alertas_con_justificacion(conexion),
        contrasenas_con_hash(conexion),
        predicciones_inmutables(),
        configuracion_segura(),
        (secretos_en_el_repositorio(archivos) if archivos is not None
         else Resultado("Sin secretos en el repositorio", "NFR-005", NO_VERIFICADO, "git no disponible aqui")),
        https_en_despliegue(url),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Revision de seguridad verificable (TASK-035).")
    parser.add_argument("--url", help="URL publica del despliegue, para comprobar HTTPS.")
    args = parser.parse_args(argv)

    from app.core.database import engine

    with engine.connect() as conexion:
        resultados = ejecutar(conexion, url=args.url)
    for r in resultados:
        print(f"[{r.estado:<13}] {r.control} ({r.requisito}): {r.detalle}")
    fallas = [r for r in resultados if r.estado == FALLA]
    print(f"\n{len(resultados)} controles: {sum(r.estado == OK for r in resultados)} OK, "
          f"{len(fallas)} con falla, {sum(r.estado == AVISO for r in resultados)} avisos, "
          f"{sum(r.estado == NO_VERIFICADO for r in resultados)} no verificados.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
