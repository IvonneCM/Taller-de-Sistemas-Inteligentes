"""
Malaria por municipio: acumulados de varios boletines -> casos por bloque
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Problema: ningun boletin trae malaria semana a semana por municipio, solo
el ACUMULADO SE1-k. Pero el equipo tiene varios boletines de 2026 con
cortes distintos (SE5, SE7, SE8, SE9, SE13). La diferencia entre dos cortes
consecutivos son los casos reportados entre ambos:

    casos(SE a..b) = acumulado(SE b) - acumulado(SE a-1)

Con los cortes disponibles salen BLOQUES: SE1-5, SE6-7, SE8, SE9, SE10-13.
Solo SE8 y SE9 son semanas individuales; el resto son bloques de varias
semanas. NUNCA se reparte un bloque en semanas inventadas: se entrega
`casos_por_semana` (promedio del bloque) marcado como tal.

Reglas de calidad (heredan la politica del proyecto: no inventar):
  - Cada fila se verifica: vivax + falciparum + mixta == total. Si no
    cuadra en el boletin impreso (p. ej. San Buenaventura en SE5) la fila
    queda `fila_inconsistente = True` y no se usa para diferencias.
  - Cada boletin se verifica: la suma de municipios debe igualar la fila
    TOTAL impresa. El resultado queda en `suma_coincide_total`.
  - Si un acumulado BAJA entre dos boletines (revision a la baja de la
    fuente), el bloque queda `revision_negativa = True` y sin casos (NaN).
  - Un municipio ausente en un boletin no se interpreta como cero: su
    primer acumulado disponible cubre SE1-k completo.

Entrada:
    data/boletines/SE05.pdf, SE07.pdf, SE08.pdf, SE09.pdf  (PDF oficiales)
    data/raw/epidemiologia/malaria_bolivia_municipal_SE01_13_2026.csv (SE13,
        ya transcrito y validado: el PDF de SE13 mezcla el texto de un grafico
        con la tabla y no es confiable de leer por texto)
Salida:
    data/processed/malaria_acumulado_por_boletin.csv
    data/processed/malaria_municipal_bloques.csv

Si los PDF no estan, el script avisa y conserva las salidas anteriores.
"""

import os
import re
import sys
import unicodedata

import pandas as pd

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLETINES_DIR = os.path.join(BASE_DIR, "data", "boletines")
SE13_CSV = os.path.join(BASE_DIR, "data", "raw", "epidemiologia", "malaria_bolivia_municipal_SE01_13_2026.csv")
OUT_ACUM = os.path.join(BASE_DIR, "data", "processed", "malaria_acumulado_por_boletin.csv")
OUT_BLOQUES = os.path.join(BASE_DIR, "data", "processed", "malaria_municipal_bloques.csv")

CORTES_PDF = {5: "SE05.pdf", 7: "SE07.pdf", 8: "SE08.pdf", 9: "SE09.pdf"}

# Orden de filas en SE5, cuyos nombres vienen partidos en varias lineas
# ("Santa Rosa del / Abuna", "Puerto Gonzalo / Moreno"). Se asigna por orden
# y se comprueba con el total impreso del boletin.
ORDEN_SE5 = [
    "RIBERALTA", "GUAYARAMERIN", "SANTA ROSA (BNI)", "REYES", "TRINIDAD",
    "SAN BUENAVENTURA", "IXIAMAS", "SENA", "PUERTO RICO", "SAN LORENZO(PND)",
    "INGAVI(HUMAITA)", "BELLA FLOR", "EUREKA(SANTOS MERCADO)", "COBIJA",
    "NACEBE(SANTA ROSA DEL ABUNA)", "VILLA NUEVA (LOMA ALTA)",
    "PUERTO GONZALO MORENO", "NUEVO MANOA(NUEVA ESPERANZA)", "PORVENIR",
    "FILADELFIA", "SAN PEDRO(PND)",
]

RE_FILA = re.compile(r"^(?P<nombre>.*?)\s*(?P<v>\d+)\s+(?P<f>\d+)\s+(?P<m>\d+)\s+(?P<t>\d+)\s*$")
RE_PREFIJO = re.compile(r"^(BENI|LA PAZ|PANDO)\s+")


def normalizar(nombre: str) -> str:
    n = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().upper().strip()
    return RE_PREFIJO.sub("", n)


def leer_tabla_pdf(ruta: str, corte: int) -> tuple[list[dict], dict | None]:
    """Devuelve (filas por municipio, fila TOTAL impresa)."""
    with pdfplumber.open(ruta) as pdf:
        texto = None
        for pg in pdf.pages:
            t = pg.extract_text() or ""
            if "Casos Confirmados de Malaria" in t and f"SE 1-{corte}" in t.replace("SE 1 - ", "SE 1-"):
                texto = t
                break
        if texto is None:
            raise ValueError(f"No encontre la tabla de malaria SE1-{corte} en {ruta}")
    lineas = texto.split("\n")
    ini = next(i for i, l in enumerate(lineas) if "VIVAX FALCIPARUM MIXTA TOTAL" in l.upper()) + 1
    filas, total = [], None
    for l in lineas[ini:]:
        m = RE_FILA.match(l.strip())
        if not m:
            continue
        reg = {k: int(m[k]) for k in ("v", "f", "m", "t")}
        if l.strip().upper().startswith(("TOTAL", "TOT AL")):
            total = reg
            break
        filas.append({"nombre_crudo": m["nombre"].strip(), **reg})
    return filas, total


def filas_a_registros(filas: list[dict], corte: int) -> list[dict]:
    if corte == 5:
        if len(filas) != len(ORDEN_SE5):
            raise ValueError(f"SE5: esperaba {len(ORDEN_SE5)} filas, lei {len(filas)}")
        nombres = ORDEN_SE5
    else:
        nombres = [normalizar(f["nombre_crudo"]) for f in filas]
    return [
        {"municipio": n, "se_corte": corte, "vivax": f["v"], "falciparum": f["f"],
         "mixta": f["m"], "total": f["t"]}
        for n, f in zip(nombres, filas)
    ]


def construir_acumulados() -> pd.DataFrame:
    registros = []
    for corte, archivo in CORTES_PDF.items():
        filas, total = leer_tabla_pdf(os.path.join(BOLETINES_DIR, archivo), corte)
        regs = filas_a_registros(filas, corte)
        suma = {k: sum(r[k] for r in regs) for k in ("vivax", "falciparum", "mixta", "total")}
        coincide = bool(total) and (suma["total"] == total["t"] and suma["vivax"] == total["v"]
                                    and suma["falciparum"] == total["f"] and suma["mixta"] == total["m"])
        print(f"SE{corte:02d}: {len(regs)} municipios | suma total={suma['total']} "
              f"| TOTAL impreso={total['t'] if total else None} | {'OK' if coincide else 'NO COINCIDE'}")
        for r in regs:
            r.update(boletin=archivo, suma_coincide_total=coincide)
        registros += regs
    # SE13: transcripcion ya validada del boletin N.13
    s13 = pd.read_csv(SE13_CSV)
    suma13 = int(s13["total_malaria"].sum())
    print(f"SE13: {len(s13)} municipios | suma total={suma13} (TOTAL impreso 1615)")
    for _, r in s13.iterrows():
        registros.append({
            "municipio": r["municipio"], "se_corte": 13, "vivax": int(r["p_vivax"]),
            "falciparum": int(r["p_falciparum"]), "mixta": int(r["mixta"]),
            "total": int(r["total_malaria"]), "boletin": "SE13 (transcripcion validada)",
            "suma_coincide_total": suma13 == 1615,
        })
    df = pd.DataFrame(registros)
    df["fila_inconsistente"] = (df["vivax"] + df["falciparum"] + df["mixta"]) != df["total"]
    return df.sort_values(["municipio", "se_corte"]).reset_index(drop=True)


def construir_bloques(acum: pd.DataFrame) -> pd.DataFrame:
    filas = []
    cols = ["vivax", "falciparum", "mixta", "total"]
    for mun, g in acum.groupby("municipio"):
        g = g.sort_values("se_corte")
        previo = None
        for _, r in g.iterrows():
            ini = 1 if previo is None else int(previo["se_corte"]) + 1
            fin = int(r["se_corte"])
            n = fin - ini + 1
            if previo is None:
                vals = {c: r[c] for c in cols}
                dudoso = bool(r["fila_inconsistente"])
            else:
                vals = {c: r[c] - previo[c] for c in cols}
                dudoso = bool(r["fila_inconsistente"] or previo["fila_inconsistente"])
            negativa = any(v < 0 for v in vals.values())
            usable = not (dudoso or negativa)
            fila = {
                "municipio": mun, "anio": 2026, "se_inicio": ini, "se_fin": fin, "n_semanas": n,
                "tipo_bloque": "semana_exacta" if n == 1 else "bloque_varias_semanas",
            }
            for c in cols:
                fila[f"casos_{c}"] = vals[c] if usable else None
            fila["casos_por_semana"] = (vals["total"] / n) if usable else None
            fila["revision_negativa"] = negativa
            fila["fila_inconsistente"] = dudoso
            fila["primer_acumulado"] = previo is None
            filas.append(fila)
            previo = r
    return pd.DataFrame(filas).sort_values(["municipio", "se_inicio"]).reset_index(drop=True)


def main():
    print("=" * 60)
    print("MALARIA: acumulados por boletin -> casos por bloque")
    print("=" * 60)
    faltan = [a for a in CORTES_PDF.values() if not os.path.exists(os.path.join(BOLETINES_DIR, a))]
    if pdfplumber is None or faltan:
        motivo = "pdfplumber no instalado" if pdfplumber is None else f"faltan PDF: {faltan}"
        print(f"AVISO: {motivo}. Se conservan las salidas anteriores.")
        return 0 if os.path.exists(OUT_BLOQUES) else 1
    acum = construir_acumulados()
    bloques = construir_bloques(acum)
    acum.to_csv(OUT_ACUM, index=False, encoding="utf-8-sig")
    bloques.to_csv(OUT_BLOQUES, index=False, encoding="utf-8-sig")
    print(f"\nAcumulados: {len(acum)} filas | Bloques: {len(bloques)} filas")
    print(f"Bloques utilizables: {int(bloques['casos_total'].notna().sum())} | "
          f"con revision negativa: {int(bloques['revision_negativa'].sum())} | "
          f"filas inconsistentes en origen: {int(bloques['fila_inconsistente'].sum())}")
    print(f"Guardado: {OUT_ACUM}\n          {OUT_BLOQUES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
