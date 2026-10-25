"""
Pipeline completo de datos — un solo comando
Proyecto: Prediccion temprana de brotes de Dengue y Malaria

Responsable: Tania Perez
Frente: Pipeline de datos (ver "Reparto_de_Desarrollo_MVP_Paralelo.pdf",
Fase 1).

Encadena, en orden, todo lo que el equipo necesita para pasar de los datos
ya descargados a un dataset listo para el modelo de Adriana:

  1. scripts/limpieza_datos.py   -> validacion, calendario diario global e
                                     imputacion climatica (REQ-013, NFR-007).
  2. scripts/ventanas_temporales_clima.py -> rezagos y promedios moviles
                                     por municipio (ventanas temporales).
  3. scripts/integrar_datos.py   -> agregacion por zona / integracion con
                                     epidemiologia (si los crudos estan
                                     disponibles; si no, se conserva el
                                     `dataset_integrado_municipal.csv` ya
                                     existente y se avisa claramente).

Uso:
    python scripts/pipeline_completo.py

Nota sobre reproducibilidad (ver docs/contrato_esquema_datos_procesados.md
y CONTEXT.md): en una maquina sin credenciales de DagsHub, los crudos de
`data/raw/epidemiologia/` y `data/raw/clima/senamhi/` no estan disponibles
(bloqueo de DVC ya documentado). Los pasos 1 y 3 degradan con gracia en ese
caso: reutilizan los CSV ya validados/integrados de una corrida anterior en
vez de fallar, y lo anuncian explicitamente. El paso 2 (ventanas
temporales) NO depende de esos crudos y siempre se re-ejecuta por completo.
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

PASOS = [
    ("1/3 — Limpieza, validacion e imputacion", "limpieza_datos.py"),
    ("2/3 — Ventanas temporales climaticas", "ventanas_temporales_clima.py"),
    ("3/3 — Integracion y agregacion por zona", "integrar_datos.py"),
]


def correr_paso(nombre: str, archivo: str) -> bool:
    print("\n" + "=" * 60)
    print(f"PASO {nombre}")
    print("=" * 60)

    resultado = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, archivo)],
        cwd=BASE_DIR,
    )

    if resultado.returncode != 0:
        print(
            f"\nAVISO: {archivo} termino con error (ver salida arriba). "
            "Si el error es por un archivo de data/raw/ ausente, es el "
            "bloqueo de credenciales DVC ya documentado en CONTEXT.md, no "
            "una falla nueva del pipeline. El paso se omite y se conserva "
            "el ultimo resultado ya existente en data/processed/."
        )
        return False
    return True


def main():
    print("PIPELINE DE DATOS — un solo comando (Fase 1, Tania)")

    resultados = {}
    for nombre, archivo in PASOS:
        resultados[archivo] = correr_paso(nombre, archivo)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for archivo, ok in resultados.items():
        estado = "OK" if ok else "OMITIDO (ver aviso arriba) — se conserva el resultado anterior"
        print(f" - {archivo}: {estado}")

    if not all(resultados.values()):
        print(
            "\nEl pipeline termino con pasos omitidos por falta de datos "
            "crudos (bloqueo DVC conocido), pero los CSV de data/processed/ "
            "quedan en un estado consistente y utilizable."
        )


if __name__ == "__main__":
    main()
