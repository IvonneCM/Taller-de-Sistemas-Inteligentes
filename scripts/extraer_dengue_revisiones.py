"""
Revisiones del dengue entre boletines: cuanto cambia un dato ya publicado
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (sesion 2026-10-25)

Los boletines declaran sus datos "provisionales". Aqui se mide cuanto: para
cada boletin con la tabla "dinamica semanal de dengue por municipio" (SE3,
5, 6, 7, 8, 9), se lee el valor de cada municipio-semana y se compara con
el valor que da el boletin N.13 (el mas reciente que tenemos).

Ejemplo real: San Borja, SE3 = 4 casos en el boletin SE3, 6 en el SE9.

Para que sirve:
  - Riesgo de datos (Fase 9, Risk Register): evidencia numerica de que el
    dato de las ultimas semanas esta subnotificado y se corrige despues.
  - Modelo (Fase 2): un modelo entrenado con el dato final no vera el dato
    provisional que tendra en produccion. Esta tabla permite estimar ese
    desfase.

Convenciones de la tabla fuente (las mismas que usa
scripts/extraer_dengue_semanal.py): una celda vacia es 0, y solo se listan
municipios con al menos un caso confirmado. Un municipio que no aparece en
un boletin anterior pero si en el SE13 se marca `ausente_en_boletin = True`
y su valor es 0 por esa convencion de la tabla (no es un dato inventado,
pero si una inferencia: queda marcada).

Verificacion: en cada fila, la suma de semanas debe igualar el total
impreso (cuando el boletin lo trae); si no, el script se detiene.

Entrada:  data/boletines/SE03.pdf ... SE09.pdf, data/processed/dengue_municipal_semanal.csv
Salida:   data/processed/dengue_revisiones_boletines.csv
          data/processed/dengue_revisiones_resumen.csv
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
FINAL_FILE = os.path.join(BASE_DIR, "data", "processed", "dengue_municipal_semanal.csv")
OUT_DETALLE = os.path.join(BASE_DIR, "data", "processed", "dengue_revisiones_boletines.csv")
OUT_RESUMEN = os.path.join(BASE_DIR, "data", "processed", "dengue_revisiones_resumen.csv")

CORTES = {3: "SE03.pdf", 5: "SE05.pdf", 6: "SE06.pdf", 7: "SE07.pdf", 8: "SE08.pdf", 9: "SE09.pdf"}


# Nombres que los boletines viejos escriben distinto que el SE13.
ALIAS = {"TARIJA": "CERCADO TJ", "CERCADO TARIJA": "CERCADO TJ"}


def norm(s: str) -> str:
    n = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().strip()
    return ALIAS.get(n, n)


def entero(x) -> int:
    return int(x) if x not in (None, "") else 0


def es_num(c) -> bool:
    return c is None or c == "" or str(c).replace(",", "").isdigit()


def leer_boletin(ruta: str, corte: int) -> pd.DataFrame | None:
    """Lee la tabla y la ACEPTA solo si pasa dos verificaciones:
    (1) en cada fila, semanas == total impreso (si el boletin trae esa
    columna); (2) cada columna de semana suma la fila 'Total' impresa.
    Si algo no cuadra devuelve None (el boletin se descarta, avisando)."""
    with pdfplumber.open(ruta) as pdf:
        tabla = None
        for pg in pdf.pages:
            t = (pg.extract_text() or "").lower()
            if "dinámica semanal de casos de dengue por municipio" in t:
                tablas = pg.extract_tables()
                if tablas:
                    tabla = max(tablas, key=len)
                    break
    if tabla is None:
        print(f"   {os.path.basename(ruta)}: no encontre la tabla")
        return None

    registros, total_fila = [], None
    for fila in tabla:
        celdas = list(fila)
        # nombre del municipio: primera celda con letras entre las 2 primeras
        idx = next((i for i in (0, 1) if celdas[i] and re.search(r"[A-Za-z]", str(celdas[i]))), None)
        if idx is None:
            valores = [c for c in celdas if c not in (None, "")]
            if valores and all(es_num(c) for c in valores) and celdas[0] in (None, ""):
                nums = [entero(c) for c in celdas[1:]] if celdas[1] not in (None,) else []
                if [str(v) for v in valores] == [str(i) for i in range(1, corte + 1)]:
                    continue  # fila de encabezado 1..k
                total_fila = [entero(c) for c in celdas if c is not None and c != ""]
            continue
        nombre = str(celdas[idx]).strip()
        if nombre.lower() in ("departamento", "municipios", "municipio"):
            continue
        resto = celdas[idx + 1:]
        if nombre.lower().startswith("total"):
            total_fila = [entero(c) for c in resto if c is not None and c != ""]
            continue
        if not all(es_num(c) for c in resto):
            continue  # encabezado con texto
        nums = [entero(c) for c in resto if c is not None]
        if len(nums) < corte:
            continue
        semanas = nums[:corte]
        if len(nums) > corte and sum(semanas) != nums[corte]:
            print(f"   {os.path.basename(ruta)}: {nombre}: semanas suman {sum(semanas)} "
                  f"y el total impreso es {nums[corte]} -> boletin descartado")
            return None
        for s, v in enumerate(semanas, start=1):
            registros.append({"municipio": norm(nombre), "semana_epidemiologica": s,
                              "casos_en_boletin": v, "corte_boletin": corte})

    df = pd.DataFrame(registros)
    if df.empty or total_fila is None:
        print(f"   {os.path.basename(ruta)}: sin fila Total impresa para verificar -> descartado")
        return None
    sumas = df.groupby("semana_epidemiologica")["casos_en_boletin"].sum().tolist()
    if sumas != total_fila[:corte]:
        print(f"   {os.path.basename(ruta)}: columnas suman {sumas} pero el Total impreso es "
              f"{total_fila[:corte]} (tabla incompleta o partida) -> descartado")
        return None
    return df


def main():
    print("=" * 60)
    print("REVISIONES DE DENGUE ENTRE BOLETINES")
    print("=" * 60)
    faltan = [a for a in CORTES.values() if not os.path.exists(os.path.join(BOLETINES_DIR, a))]
    if pdfplumber is None or faltan:
        motivo = "pdfplumber no instalado" if pdfplumber is None else f"faltan PDF: {faltan}"
        print(f"AVISO: {motivo}. Se conservan las salidas anteriores.")
        return 0 if os.path.exists(OUT_DETALLE) else 1

    final = pd.read_csv(FINAL_FILE)[["municipio", "semana_epidemiologica", "casos_dengue"]]
    final = final.rename(columns={"casos_dengue": "casos_final_se13"})
    final["municipio"] = final["municipio"].map(norm)

    partes = []
    for corte, archivo in CORTES.items():
        b = leer_boletin(os.path.join(BOLETINES_DIR, archivo), corte)
        if b is None:
            print(f"SE{corte:02d}: DESCARTADO (no pasa la verificacion contra el total impreso)")
            continue
        print(f"SE{corte:02d}: OK {b['municipio'].nunique()} municipios, {len(b)} celdas, "
              f"columnas = Total impreso")
        # Universo completo: todos los municipios del SE13 en las semanas <= corte
        base = final[final["semana_epidemiologica"] <= corte].merge(
            b, on=["municipio", "semana_epidemiologica"], how="left"
        )
        base["ausente_en_boletin"] = base["casos_en_boletin"].isna()
        base["casos_en_boletin"] = base["casos_en_boletin"].fillna(0).astype(int)
        base["corte_boletin"] = corte
        partes.append(base)
        extra = set(b["municipio"]) - set(final["municipio"])
        if extra:
            print(f"   AVISO: municipios en SE{corte} que no estan en SE13: {sorted(extra)}")

    det = pd.concat(partes, ignore_index=True)
    det["diferencia"] = det["casos_final_se13"] - det["casos_en_boletin"]
    det["semanas_de_antiguedad"] = det["corte_boletin"] - det["semana_epidemiologica"]
    det = det[["corte_boletin", "municipio", "semana_epidemiologica", "semanas_de_antiguedad",
               "casos_en_boletin", "casos_final_se13", "diferencia", "ausente_en_boletin"]]
    det.to_csv(OUT_DETALLE, index=False, encoding="utf-8-sig")

    res = det.groupby("corte_boletin").agg(
        celdas=("diferencia", "size"),
        celdas_revisadas=("diferencia", lambda s: int((s != 0).sum())),
        casos_en_boletin=("casos_en_boletin", "sum"),
        casos_final_se13=("casos_final_se13", "sum"),
    ).reset_index()
    res["casos_agregados_despues"] = res["casos_final_se13"] - res["casos_en_boletin"]
    res["porcentaje_subnotificado"] = (100 * res["casos_agregados_despues"] / res["casos_final_se13"]).round(1)
    res.to_csv(OUT_RESUMEN, index=False, encoding="utf-8-sig")

    print("\nResumen por boletin (que parte del dato final faltaba en ese boletin):")
    print(res.to_string(index=False))
    # Rezago: cuanto se corrige segun la antiguedad de la semana
    rez = det[det["corte_boletin"].isin([7, 8, 9])].groupby("semanas_de_antiguedad").agg(
        casos_en_boletin=("casos_en_boletin", "sum"), casos_final=("casos_final_se13", "sum"))
    rez["pct_visto"] = (100 * rez["casos_en_boletin"] / rez["casos_final"]).round(1)
    print("\nPorcentaje del dato final ya visible segun antiguedad de la semana (SE7-9):")
    print(rez.head(6).to_string())
    print(f"\nGuardado: {OUT_DETALLE}\n          {OUT_RESUMEN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
