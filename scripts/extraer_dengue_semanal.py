"""
Extraccion de la serie semanal de dengue por municipio
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez (hallazgo de sesion 2026-10-25: el Boletin
Epidemiologico N.13 del Ministerio de Salud y Deportes SI trae un
desglose semana a semana por municipio para dengue -- columnas SE1 a
SE13 -- que el pipeline original no extraia, solo tomaba la columna
"Total de Casos confirmados". Esto resuelve el vacio critico #2 de
docs/inventario_datos.md ("Obtener casos semana-a-semana por municipio").

IMPORTANTE -- esto aplica SOLO a dengue, no a malaria:
La tabla de malaria del mismo boletin (y de otros boletines semanales
revisados: N.5, N.9, N.40) NUNCA trae columnas semanales por municipio,
solo un acumulado unico (VIVAX, FALCIPARUM, MIXTA, TOTAL). Malaria se
queda como acumulado SE1-13 por municipio -- no es un error de este
script, es una limitacion real de la fuente, confirmada en 3 boletines
distintos de distintas epocas del año.

Fuente: Ministerio de Salud y Deportes de Bolivia, Boletin Epidemiologico
Semana Epidemiologica N.13, 2026 (pagina 8), descargado de
https://www.minsalud.gob.bo/9104-boletines-epidemiologicos-2026

Entrada: data/boletines/SE13.pdf (o la ruta historica en data/raw/epidemiologia/)
Salida: data/processed/dengue_municipal_semanal.csv (formato largo:
una fila por municipio-semana)

Verificacion incluida: la suma de casos por semana (columna a columna)
y el total general deben coincidir EXACTO con los totales impresos en
el boletin (fila "Total Casos" y columna "Total de Casos confirmados").
Si no coinciden, el script se detiene -- no se guarda nada a medias.
"""

import os
import sys

import pandas as pd
import pdfplumber


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ubicacion actual de los boletines: data/boletines/. Se acepta tambien la
# ruta historica (data/raw/epidemiologia/) por compatibilidad.
_PDF_CANDIDATOS = [
    os.path.join(BASE_DIR, "data", "boletines", "SE13.pdf"),
    os.path.join(BASE_DIR, "data", "raw", "epidemiologia", "boletin_epidemiologico_SE13_2026.pdf"),
]
PDF_FILE = next((p for p in _PDF_CANDIDATOS if os.path.exists(p)), _PDF_CANDIDATOS[0])

# Reusa el archivo ya validado para heredar el departamento de cada
# municipio sin tener que volver a transcribirlo a mano (menos riesgo
# de error de tipeo en 28 nombres).
DENGUE_VALIDADO_FILE = os.path.join(
    BASE_DIR, "data", "processed", "dengue_municipal_validado.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR, "data", "processed", "dengue_municipal_semanal.csv"
)

PAGINA_TABLA = 8  # 1-indexada, tal como se cita en el resto del proyecto
ANIO = 2026
N_SEMANAS = 13

FUENTE = "Ministerio de Salud y Deportes de Bolivia, Boletin Epidemiologico N13, 2026"


# ============================================================
# EXTRACCION
# ============================================================

def extraer_tabla():
    with pdfplumber.open(PDF_FILE) as pdf:
        pagina = pdf.pages[PAGINA_TABLA - 1]
        tablas = pagina.find_tables()

        if len(tablas) != 1:
            print(
                f"ERROR: se esperaba 1 tabla en la pagina {PAGINA_TABLA}, "
                f"se encontraron {len(tablas)}. El layout del PDF pudo "
                "haber cambiado -- revisar manualmente antes de confiar "
                "en la extraccion."
            )
            sys.exit(1)

        datos = tablas[0].extract()

    return datos


def validar_y_separar(datos):
    """La ultima fila es el total nacional por semana (sin nombre de
    municipio). Se usa solo para verificar, no se guarda."""

    fila_total = datos[-1]
    filas_municipio = datos[:-1]

    if fila_total[0] not in (None, ""):
        print(
            "ERROR: la ultima fila de la tabla no parece ser el total "
            f"nacional (primera celda = {fila_total[0]!r}). Revisar "
            "manualmente el PDF -- el layout pudo haber cambiado."
        )
        sys.exit(1)

    return filas_municipio, fila_total


def construir_formato_largo(filas_municipio):
    registros = []

    for fila in filas_municipio:
        municipio = fila[0]
        casos_semanales = fila[1 : 1 + N_SEMANAS]
        total_impreso = fila[1 + N_SEMANAS]

        suma_fila = 0
        for semana, valor in enumerate(casos_semanales, start=1):
            casos = int(valor) if valor not in (None, "") else 0
            suma_fila += casos
            registros.append(
                {
                    "municipio": municipio,
                    "anio": ANIO,
                    "semana_epidemiologica": semana,
                    "casos_dengue": casos,
                }
            )

        total_esperado = int(total_impreso) if total_impreso not in (None, "") else 0
        if suma_fila != total_esperado:
            print(
                f"ERROR: {municipio} -- suma de semanas ({suma_fila}) no "
                f"coincide con el total impreso en el boletin "
                f"({total_esperado}). No se guarda nada hasta corregir."
            )
            sys.exit(1)

    return pd.DataFrame(registros)


def verificar_contra_totales_nacionales(df_largo, fila_total):
    suma_por_semana = (
        df_largo.groupby("semana_epidemiologica")["casos_dengue"].sum().sort_index()
    )
    esperado_por_semana = [int(x) for x in fila_total[1 : 1 + N_SEMANAS]]

    if list(suma_por_semana.values) != esperado_por_semana:
        print("ERROR: la suma nacional por semana no coincide con la fila 'Total Casos' del boletin.")
        print("Calculado:", list(suma_por_semana.values))
        print("Esperado: ", esperado_por_semana)
        sys.exit(1)

    total_general = df_largo["casos_dengue"].sum()
    total_esperado = int(fila_total[1 + N_SEMANAS])
    if total_general != total_esperado:
        print(
            f"ERROR: total general calculado ({total_general}) no coincide "
            f"con el total del boletin ({total_esperado})."
        )
        sys.exit(1)

    print("Verificacion OK: suma por semana y total general coinciden exacto con el boletin impreso.")
    print(f" - Total general: {total_general} casos (SE1-{N_SEMANAS}, {ANIO})")


def agregar_departamento_y_fuente(df_largo):
    dengue_validado = pd.read_csv(DENGUE_VALIDADO_FILE)
    mapa_departamento = dengue_validado.set_index("municipio")["departamento"].to_dict()

    sin_mapa = set(df_largo["municipio"]) - set(mapa_departamento)
    if sin_mapa:
        print(
            f"ERROR: {len(sin_mapa)} municipio(s) de la tabla semanal no "
            f"estan en dengue_municipal_validado.csv: {sorted(sin_mapa)}. "
            "No se puede asignar departamento con certeza -- revisar antes "
            "de continuar."
        )
        sys.exit(1)

    df_largo["departamento"] = df_largo["municipio"].map(mapa_departamento)
    df_largo["fuente"] = FUENTE
    df_largo["pagina_fuente"] = PAGINA_TABLA
    df_largo["periodo_dato"] = f"SE {df_largo['semana_epidemiologica'].min()}-{df_largo['semana_epidemiologica'].max()}"

    columnas = [
        "departamento",
        "municipio",
        "anio",
        "semana_epidemiologica",
        "casos_dengue",
        "fuente",
        "pagina_fuente",
        "periodo_dato",
    ]
    return df_largo[columnas]


def main():
    print("=" * 60)
    print("EXTRACCION: serie semanal de dengue por municipio (SE1-13, 2026)")
    print("=" * 60)

    datos = extraer_tabla()
    filas_municipio, fila_total = validar_y_separar(datos)

    print(f"\nMunicipios extraidos: {len(filas_municipio)}")

    df_largo = construir_formato_largo(filas_municipio)
    verificar_contra_totales_nacionales(df_largo, fila_total)

    df_final = agregar_departamento_y_fuente(df_largo)
    df_final.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\nFilas municipio-semana generadas: {len(df_final)}")
    print(f"Guardado en: {OUTPUT_FILE}")

    print("\nNOTA: esto aplica solo a dengue. La tabla de malaria del mismo")
    print("boletin NO trae desglose semanal (confirmado en N.5, N.9, N.13,")
    print("N.40) -- malaria se mantiene como acumulado SE1-13 por municipio.")


if __name__ == "__main__":
    main()
