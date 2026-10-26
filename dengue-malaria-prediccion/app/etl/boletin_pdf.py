"""Lectura de un Boletin Epidemiologico (PDF) subido por una persona (REQ-014, REQ-013).

Por que existe: el sitio del Ministerio de Salud bloquea la descarga automatica,
asi que la ingesta de un boletin nuevo la inicia una persona subiendo el PDF.
Este modulo solo LEE y VALIDA; no toca la base de datos (eso lo hace
app/services/boletines.py).

Que se extrae: la tabla "Dinamica semanal de casos de dengue por municipio",
que trae las semanas 1..N del boletin N (las anteriores ya corregidas). Es la
misma tabla que usan scripts/extraer_dengue_semanal.py (boletin 13) y
scripts/extraer_dengue_revisiones.py (boletines 3 a 9).

Reglas para no inventar datos (CLAUDE.md regla 1):
  - La semana y el anio salen de la portada ("Semana Epidemiologica N.º k 2026").
  - Celda vacia = 0 casos: es la convencion de la tabla, que solo lista
    municipios con al menos un caso.
  - Se acepta la tabla SOLO si cuadra con lo impreso: cada fila con su total
    (si el boletin lo trae) y cada columna con la fila de totales. Si algo no
    cuadra (tabla partida entre paginas, formato nuevo, etc.) se rechaza
    entera con un mensaje claro; nunca se guarda una parte.
  - Malaria no se extrae: el boletin no trae serie semanal (ADR-005).

Formatos vistos (2026): con o sin columna de departamento (SE 3), con o sin
columna de total y de tasa (SE 13), y tablas partidas en varias (SE 5). El
boletin SE 21 ya no trae la tabla municipal: solo totales por departamento.

Sin pandas: la imagen `api` no lo instala (tests/test_api_ligera.py).
"""

from __future__ import annotations

import io
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

TITULO_TABLA = "dinámica semanal de casos de dengue por municipio"
MAX_PAGINAS = 80
_PORTADA = re.compile(r"semana\s+epidemiol[oó]gica\s*n\s*[º°o.]?\s*(\d{1,2})\s+(20\d{2})", re.IGNORECASE)
# Nombres que algunos boletines escriben distinto (mismo criterio que
# scripts/extraer_dengue_revisiones.py).
ALIAS = {"TARIJA": "CERCADO TJ", "CERCADO TARIJA": "CERCADO TJ"}


class BoletinInvalido(ValueError):
    """El archivo no se puede usar; el mensaje es para la persona que lo subio."""


@dataclass(frozen=True)
class FilaMunicipio:
    nombre: str          # tal como lo imprime el boletin
    clave: str           # normalizado para cruzar con el catalogo
    semanas: list[int]   # casos de las semanas 1..N


@dataclass(frozen=True)
class ExtraccionBoletin:
    semana: int          # N: numero del boletin (ultima semana que cubre)
    anio: int
    pagina: int          # 1-indexada, para auditar a mano
    municipios: list[FilaMunicipio]
    totales_semana: list[int]

    @property
    def total(self) -> int:
        return sum(self.totales_semana)


def normalizar_municipio(nombre: str) -> str:
    """Mayusculas, sin tildes ni espacios repetidos; aplica ALIAS."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    clave = " ".join(sin_tildes.upper().split())
    return ALIAS.get(clave, clave)


def _texto(celda) -> str:
    return " ".join(str(celda).split()) if celda is not None else ""


def _tiene_letras(texto: str) -> bool:
    return bool(re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", texto))


def _entero(texto: str) -> int | None:
    """'' -> 0 (celda vacia), '12' -> 12; cualquier otra cosa -> None."""
    if texto == "":
        return 0
    return int(texto) if texto.isdigit() else None


def _leer_portada(pdf) -> tuple[int, int]:
    portada = " ".join((pdf.pages[0].extract_text() or "").split())
    if "BOLET" not in portada.upper() or "EPIDEMIOL" not in portada.upper():
        raise BoletinInvalido("El archivo no parece un Boletín Epidemiológico del Ministerio de Salud.")
    m = _PORTADA.search(portada)
    if not m:
        raise BoletinInvalido("No se encontró en la portada la semana epidemiológica del boletín.")
    semana, anio = int(m.group(1)), int(m.group(2))
    if not 1 <= semana <= 53:
        raise BoletinInvalido(f"La portada indica una semana fuera de rango ({semana}).")
    return semana, anio


def _buscar_tabla(pdf, semana: int) -> tuple[int, list[list]]:
    for numero, pagina in enumerate(pdf.pages, start=1):
        if TITULO_TABLA in (pagina.extract_text() or "").lower():
            tablas = pagina.extract_tables()
            if tablas:
                return numero, max(tablas, key=len)
    raise BoletinInvalido(
        f"El boletín de la semana {semana} no trae la tabla «Dinámica semanal de casos de "
        "dengue por municipio». Los boletines más recientes solo publican totales por "
        "departamento, que no sirven para el modelo municipal."
    )


def _interpretar(tabla: list[list], semana: int) -> tuple[list[FilaMunicipio], list[int]]:
    filas = [[_texto(c) for c in fila] for fila in tabla]
    secuencia = [str(i) for i in range(1, semana + 1)]

    # 1) Filas de municipio: la etiqueta es la ultima celda con letras entre las
    #    dos primeras (si hay columna de departamento, el municipio es la 2.ª).
    municipios: list[tuple[str, int, list[str]]] = []
    candidatas_total: list[list[str]] = []
    for celdas in filas:
        etiquetas = [i for i in range(min(2, len(celdas))) if _tiene_letras(celdas[i])]
        if not etiquetas:
            valores = [c for c in celdas if c]
            if valores and valores[: len(secuencia)] != secuencia:
                candidatas_total.append(celdas)
            continue
        idx = etiquetas[-1]
        nombre = celdas[idx]
        if nombre.lower().startswith("total") or celdas[0].lower().startswith("total"):
            candidatas_total.append(celdas)
            continue
        if nombre.lower() in ("departamento", "departamentos", "municipio", "municipios") or "semana" in nombre.lower():
            continue
        municipios.append((nombre, idx + 1, celdas))

    if not municipios:
        raise BoletinInvalido("La tabla de dengue por municipio está vacía o no se pudo leer.")
    # Columna donde empiezan las semanas: la mas comun entre las filas de municipio.
    inicio = Counter(i for _, i, _ in municipios).most_common(1)[0][0]

    resultado: list[FilaMunicipio] = []
    for nombre, _, celdas in municipios:
        valores = [_entero(c) for c in celdas[inicio: inicio + semana]]
        if len(valores) < semana or None in valores:
            raise BoletinInvalido(
                f"La fila de {nombre} no tiene {semana} semanas numéricas: la tabla pudo "
                "cambiar de formato. Revisar el PDF a mano."
            )
        impreso = _entero(celdas[inicio + semana]) if len(celdas) > inicio + semana else None
        if impreso not in (None, 0) and impreso != sum(valores):
            raise BoletinInvalido(
                f"{nombre}: las semanas suman {sum(valores)} y el total impreso es {impreso}. "
                "No se guarda nada."
            )
        resultado.append(FilaMunicipio(nombre=nombre, clave=normalizar_municipio(nombre), semanas=valores))

    repetidos = [c for c, n in Counter(f.clave for f in resultado).items() if n > 1]
    if repetidos:
        raise BoletinInvalido(f"Municipios repetidos en la tabla: {', '.join(sorted(repetidos))}.")

    # 2) Fila de totales impresa: sin ella no hay contra que verificar.
    totales = None
    for celdas in candidatas_total:
        valores = [_entero(c) for c in celdas[inicio: inicio + semana]]
        if len(valores) == semana and None not in valores and any(celdas[inicio: inicio + semana]):
            totales = valores
    if totales is None:
        raise BoletinInvalido(
            "No se encontró la fila de totales impresa (o está incompleta), así que no se "
            "puede verificar la tabla. No se guarda nada."
        )
    calculado = [sum(f.semanas[i] for f in resultado) for i in range(semana)]
    if calculado != totales:
        raise BoletinInvalido(
            "La suma por semana no coincide con la fila de totales del boletín "
            f"(calculado {calculado}, impreso {totales}). La tabla puede estar partida "
            "entre páginas. No se guarda nada."
        )
    return resultado, totales


def extraer_boletin(contenido: bytes) -> ExtraccionBoletin:
    """Lee el PDF y devuelve la tabla verificada, o lanza BoletinInvalido."""
    import pdfplumber  # solo al usarse: no carga nada pesado al importar la app
    from pdfminer.psparser import PSException
    from pdfplumber.utils.exceptions import PdfminerException

    if not contenido.startswith(b"%PDF-"):
        raise BoletinInvalido("El archivo no es un PDF.")
    try:
        with pdfplumber.open(io.BytesIO(contenido)) as pdf:
            if not pdf.pages:
                raise BoletinInvalido("El PDF no tiene páginas.")
            if len(pdf.pages) > MAX_PAGINAS:
                raise BoletinInvalido(f"El PDF tiene {len(pdf.pages)} páginas; un boletín tiene menos de {MAX_PAGINAS}.")
            semana, anio = _leer_portada(pdf)
            pagina, tabla = _buscar_tabla(pdf, semana)
    except BoletinInvalido:
        raise
    except (PdfminerException, PSException, ValueError, KeyError, TypeError) as error:
        raise BoletinInvalido("El archivo no se pudo leer como PDF.") from error

    municipios, totales = _interpretar(tabla, semana)
    return ExtraccionBoletin(semana=semana, anio=anio, pagina=pagina, municipios=municipios, totales_semana=totales)
