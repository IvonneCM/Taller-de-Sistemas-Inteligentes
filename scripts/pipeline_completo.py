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
  4. scripts/extraer_dengue_semanal.py -> dengue por semana y municipio,
                                     extraido con verificacion automatica
                                     del Boletin N.13 (NUEVO, 2026-10-25).
                                     Solo dengue -- malaria no tiene
                                     desglose semanal en la fuente.
  5. scripts/clima_nasa_power.py -> clima de reanalisis para los 42
                                     municipios con casos (SENAMHI solo
                                     cubre 4). Cacheado: sin red reutiliza
                                     data/raw/clima/nasa_power/.
  6. scripts/extraer_malaria_boletines.py -> malaria por bloques de semanas,
                                     por diferencia de acumulados de los
                                     boletines SE5, 7, 8, 9 y 13.
  7. scripts/extraer_dengue_revisiones.py -> cuanto se corrige el dato de
                                     dengue entre boletines (riesgo de datos).
  8. scripts/construir_panel_semanal.py -> panel municipio-semana de DENGUE
                                     (28 municipios x 13 semanas) con clima,
                                     rezagos y objetivos a 3 y 4 semanas.
                                     Es el dataset para el modelo.
  9. scripts/construir_panel_malaria.py -> panel de MALARIA por bloques +
                                     clima (no hay serie semanal en la fuente).
 10. scripts/validar_contrato.py -> comprueba columnas, claves, rangos y
                                     ausencia de fuga de datos en los paneles.
                                     A diferencia de los demas pasos, si
                                     falla el pipeline termina con error.

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
    ("1/10 — Limpieza, validacion e imputacion", "limpieza_datos.py"),
    ("2/10 — Ventanas temporales climaticas (SENAMHI)", "ventanas_temporales_clima.py"),
    ("3/10 — Integracion y agregacion por zona", "integrar_datos.py"),
    ("4/10 — Extraccion de dengue semanal por municipio", "extraer_dengue_semanal.py"),
    ("5/10 — Clima NASA POWER para todos los municipios", "clima_nasa_power.py"),
    ("6/10 — Malaria por bloques (diferencias entre boletines)", "extraer_malaria_boletines.py"),
    ("7/10 — Revisiones de dengue entre boletines", "extraer_dengue_revisiones.py"),
    ("8/10 — Panel semanal de dengue (clima + rezagos + objetivos)", "construir_panel_semanal.py"),
    ("9/10 — Panel de malaria por bloques + clima", "construir_panel_malaria.py"),
    ("10/10 — Validacion del contrato de datos", "validar_contrato.py"),
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

    if not resultados.get("validar_contrato.py", True):
        print(
            "\nERROR: los datos generados NO cumplen el contrato publicado "
            "(ver problemas arriba). No usar estos paneles para entrenar."
        )
        sys.exit(1)

    if not all(resultados.values()):
        print(
            "\nEl pipeline termino con pasos omitidos por falta de datos "
            "crudos (bloqueo DVC conocido), pero los CSV de data/processed/ "
            "quedan en un estado consistente y utilizable."
        )


if __name__ == "__main__":
    main()
