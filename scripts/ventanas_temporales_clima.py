"""
Ventanas temporales climaticas (rezagos y promedios moviles)
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez
Frente: Pipeline de datos (reparto "Reparto_de_Desarrollo_MVP_Paralelo")

Este script toma la serie semanal de clima ya validada e imputada por
scripts/limpieza_datos.py (data/processed/clima_semanal_calidad.csv) y
construye las "ventanas temporales" que el modelo de Adriana necesita:
rezagos (lag) de 1 a 4 semanas y promedios moviles de 2 a 4 semanas, por
municipio, para temperatura, humedad y precipitacion.

IMPORTANTE sobre que SI y que NO se puede ventanear con los datos actuales:
- El CLIMA si tiene resolucion semanal real por municipio (11 semanas,
  SE3-SE13 2026) -> los rezagos y promedios moviles de este script son
  validos y no inventan nada.
- Los CASOS epidemiologicos NO tienen esa resolucion (son un acumulado
  SE1-13 por municipio, ver docs/resultados_linea_base.md Exp. D) -> este
  script NO genera rezagos de casos ni finge una serie epidemiologica
  semanal que no existe. Eso sigue siendo una limitacion conocida del
  proyecto (REQ-014/TASK-009), no algo que este script resuelva.

Salida: data/processed/clima_semanal_ventanas.csv (contrato de esquema
publicado en docs/contrato_esquema_datos_procesados.md).
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLIMA_SEMANAL_CALIDAD = os.path.join(
    BASE_DIR, "data", "processed", "clima_semanal_calidad.csv"
)
OUTPUT_FILE = os.path.join(
    BASE_DIR, "data", "processed", "clima_semanal_ventanas.csv"
)

VARIABLES = ["temperatura_media", "humedad_media", "precipitacion_total_mm"]
REZAGOS_SEMANAS = [1, 2, 3, 4]
VENTANAS_MOVILES = [2, 3, 4]


def construir_ventanas(df: pd.DataFrame) -> pd.DataFrame:
    datos = df.copy()
    datos = datos.sort_values(["municipio", "anio", "semana_epidemiologica"])

    resultado = []
    for municipio, grupo in datos.groupby("municipio"):
        grupo = grupo.sort_values(["anio", "semana_epidemiologica"]).reset_index(drop=True)

        for variable in VARIABLES:
            for r in REZAGOS_SEMANAS:
                grupo[f"{variable}_lag{r}"] = grupo[variable].shift(r)
            for v in VENTANAS_MOVILES:
                # ventana solo con semanas pasadas (incluye la actual), nunca futuras
                grupo[f"{variable}_media_movil_{v}sem"] = (
                    grupo[variable].rolling(window=v, min_periods=1).mean()
                )

        resultado.append(grupo)

    completo = pd.concat(resultado, ignore_index=True)

    columnas_lag = [c for c in completo.columns if "_lag" in c or "_media_movil_" in c]
    completo["semanas_historia_disponible"] = (
        completo.groupby("municipio").cumcount() + 1
    )
    completo["ventana_completa_4_semanas"] = completo["semanas_historia_disponible"] >= 4

    return completo


def main():
    print("\n==========================================")
    print("VENTANAS TEMPORALES CLIMATICAS (lag + rolling)")
    print("==========================================")

    df = pd.read_csv(CLIMA_SEMANAL_CALIDAD)
    print(f"Entrada: {CLIMA_SEMANAL_CALIDAD} ({len(df)} filas)")

    resultado = construir_ventanas(df)

    resultado.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Salida: {OUTPUT_FILE} ({len(resultado)} filas, {len(resultado.columns)} columnas)")

    completas = int(resultado["ventana_completa_4_semanas"].sum())
    print(f"Filas con las 4 semanas de historia completas: {completas} de {len(resultado)}")

    print("\n==========================================")
    print("COMPLETADO")
    print("==========================================")


if __name__ == "__main__":
    main()
