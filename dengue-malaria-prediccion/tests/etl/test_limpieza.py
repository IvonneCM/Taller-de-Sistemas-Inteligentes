"""Verificacion de TASK-010: 'test unitario con dataset que tiene 20% de
valores faltantes; el resultado no contiene NaN y se marca el flag de
confianza baja cuando corresponde'."""

import pandas as pd

from app.etl.limpieza import (
    calcular_porcentaje_faltante,
    imputar_y_marcar_clima,
    nivel_confianza,
    resumen_calidad_por_municipio,
)


def _dataset_10_dias_dos_municipios(huecos_a):
    """10 dias x 2 municipios = 20 observaciones. `huecos_a` es la lista de
    posiciones (indice de dia, 0-9) que se vacian en el municipio A; el
    municipio B queda completo, para que el paso 3 (vecino mas cercano)
    pueda resolver esos huecos sin dejar NaN."""

    fechas = pd.date_range("2026-02-01", periods=10, freq="D")
    filas = []
    for i, fecha in enumerate(fechas):
        temp_a = None if i in huecos_a else 28.0 + i * 0.1
        filas.append({"municipio": "A", "fecha": fecha, "temperatura_media_c": temp_a})
        filas.append({"municipio": "B", "fecha": fecha, "temperatura_media_c": 27.5 + i * 0.1})
    return pd.DataFrame(filas)


def test_nivel_confianza_umbrales_nfr007():
    assert nivel_confianza(0) == "confianza_normal"
    assert nivel_confianza(5) == "confianza_normal"
    assert nivel_confianza(5.1) == "confianza_baja"
    assert nivel_confianza(20) == "confianza_baja"
    assert nivel_confianza(20.1) == "datos_insuficientes"


def test_calcular_porcentaje_faltante():
    serie = pd.Series([1.0, None, 3.0, None, 5.0])
    assert calcular_porcentaje_faltante(serie) == 40.0


def test_imputacion_con_20pct_faltante_no_deja_nan_y_marca_confianza_baja():
    # 20% de huecos en el municipio A: 2 de 10 dias. Uno interpolable
    # (hueco interno de 1 dia -> paso 1), otro al borde de la serie, donde
    # la interpolacion interna no aplica y debe resolverse por el municipio
    # vecino (paso 3).
    huecos_a = [3, 9]
    df = _dataset_10_dias_dos_municipios(huecos_a)

    resumen = resumen_calidad_por_municipio(df, "temperatura_media_c")
    fila_a = resumen.loc[resumen["municipio"] == "A"].iloc[0]
    assert fila_a["porcentaje_faltante"] == 20.0
    assert fila_a["nivel_confianza"] == "confianza_baja"

    coordenadas = {"A": (-10.8, -65.3), "B": (-10.9, -65.4)}
    imputado = imputar_y_marcar_clima(df, coordenadas, variables=["temperatura_media_c"])

    assert imputado["temperatura_media_c"].isna().sum() == 0

    filas_a = imputado[imputado["municipio"] == "A"]
    assert filas_a["es_dato_imputado"].sum() == 2  # los 2 huecos originales

    metodo_interpolado = filas_a.loc[filas_a["temperatura_media_c_metodo"] == "interpolacion_lineal"]
    metodo_vecino = filas_a[filas_a["temperatura_media_c_metodo"].str.startswith("mediana_municipio_vecino")]
    assert len(metodo_interpolado) == 1
    assert len(metodo_vecino) == 1

    filas_b = imputado[imputado["municipio"] == "B"]
    assert filas_b["es_dato_imputado"].sum() == 0


def test_imputacion_no_toca_filas_completamente_observadas():
    df = _dataset_10_dias_dos_municipios(huecos_a=[])
    coordenadas = {"A": (-10.8, -65.3), "B": (-10.9, -65.4)}

    imputado = imputar_y_marcar_clima(df, coordenadas, variables=["temperatura_media_c"])

    assert imputado["es_dato_imputado"].sum() == 0
    assert imputado["temperatura_media_c"].isna().sum() == 0
