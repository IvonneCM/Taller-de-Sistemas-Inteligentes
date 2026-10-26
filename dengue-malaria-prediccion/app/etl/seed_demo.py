"""Datos de demostracion reproducibles (TASK-038 / REQ-001, REQ-002).

Deja la base lista para recorrer el flujo completo con UN comando:

    SEED_DEMO_PASSWORD=<clave-de-demo> python -m app.etl.seed_demo

Con `--todos-los-municipios` se amplia antes el catalogo (28 municipios con
dengue y 21 con malaria, ADR-007); sin esa opcion, solo la zona piloto.

Pasos (cada uno es idempotente salvo el ultimo, ver abajo):
  1. catalogo (departamentos, enfermedades, zona piloto) y usuarios demo
     `@demo.local` con los 5 roles (app/etl/seed_usuarios.py);
  2. casos observados REALES del boletin N.o 13 (dengue semanal y malaria
     acumulada) desde data/processed, si esos CSV existen;
  3. registro del modelo baseline de dengue en `modelos`, con las metricas
     reales de TASK-012 (marcadas como estimadas en su metadata);
  4. predicciones: se ejecuta el pipeline REAL de TASK-014 sobre el panel
     semanal real y se persisten las de los municipios del catalogo.

Que NO se inventa (CLAUDE.md regla 1):
  - No hay predicciones de malaria: no existe modelo de malaria (solo hay
    acumulados SE1-13, ADR-005). La malaria se muestra con casos observados.
  - No se cargan brotes confirmados: no hay fuente de brotes.
  - Las alertas NO se inventan: las crea evaluacion_alertas (TASK-015) con el
    umbral vigente (70 % por defecto, valor referencial de REQ-009). Con las
    predicciones actuales (15 a 44 %) no se emite ninguna; para ver alertas, un
    admin baja el umbral (POST /admin/umbrales) y se ejecuta
    `python -m app.ml.evaluacion_alertas`.
  - La fecha de generacion es la del momento de ejecucion (o `--fecha`), no la
    de los datos: el panel cubre SE1-13 de 2026.

`predicciones` es inmutable (NFR-009): volver a ejecutar sin `--forzar` NO
agrega filas si el modelo ya tiene predicciones; con `--forzar` agrega una
nueva tanda (la API usa siempre la mas reciente por zona).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.etl import seed_catalogo, seed_usuarios
from app.ml import entrenamiento, prediccion
from app.ml.job_semanal import asegurar_modelo
from app.etl.conectores import epidemiologia
from app.ml.features import cargar_features
from app.models import Modelo, Prediccion

# <repo>/data/processed. En la imagen Docker `ml` no existe (solo se copia app/):
# alli la ingesta de casos se omite y se avisa.
PROCESADOS = Path(__file__).resolve().parents[3] / "data" / "processed"


def _ingerir_casos(db, procesados: Path) -> dict:
    """Casos observados reales (idempotente: la ingesta no duplica)."""
    dengue = procesados / "dengue_municipal_semanal.csv"
    malaria = procesados / "malaria_municipal_validado.csv"
    if not (dengue.exists() and malaria.exists()):
        return {"omitida": f"no se encontraron los CSV procesados en {procesados}"}
    return {
        "dengue_semanal": epidemiologia.ingerir_dengue_semanal(
            db, epidemiologia.leer_dengue_semanal_csv(str(dengue))
        ),
        "malaria_acumulada": epidemiologia.ingerir_epidemiologia_acumulada(
            db, epidemiologia.leer_epidemiologia_municipal_csv(str(malaria), "malaria"), "malaria"
        ),
    }


def sembrar_demo(
    *,
    password: str | None = None,
    fecha_generacion: datetime | date | None = None,
    version: str | None = None,
    forzar: bool = False,
    panel: Path | None = None,
    directorio: Path | None = None,
    procesados: Path | None = None,
    db=None,
) -> dict:
    propio = db is None
    if propio:
        db = SessionLocal()
    version = version or entrenamiento.MODEL_VERSION
    directorio = Path(directorio) if directorio else entrenamiento.ARTIFACTS_DIR
    try:
        seed_catalogo.seed(db=db)
        usuarios = seed_usuarios.seed(password, db=db)
        casos = _ingerir_casos(db, Path(procesados) if procesados else PROCESADOS)

        modelo_id, modelo_creado = asegurar_modelo(db, version, directorio)

        ya_tiene = db.scalar(
            select(func.count()).select_from(Prediccion).where(Prediccion.modelo_id == modelo_id)
        )
        if ya_tiene and not forzar:
            resumen = {"insertadas": [], "omitidas": [], "no_publicadas": 0,
                       "motivo": "el modelo ya tiene predicciones (use --forzar)"}
        else:
            resultado = cargar_features(panel) if panel is not None else cargar_features()
            calculadas = prediccion.generar_predicciones(
                resultado,
                horizonte=prediccion.HORIZONTE_PUBLICADO,
                fecha_generacion=fecha_generacion,
                version=version,
                directorio=directorio,
            )
            resumen = prediccion.persistir_predicciones(
                calculadas, modelo_id=modelo_id, session=db, evaluar_alertas=True
            )

        if propio:
            db.commit()
        return {
            "usuarios": usuarios,
            "casos": casos,
            "modelo_id": modelo_id,
            "modelo_creado": modelo_creado,
            "predicciones_insertadas": len(resumen["insertadas"]),
            "predicciones_omitidas": resumen["omitidas"],
            "predicciones_no_publicadas": resumen["no_publicadas"],
            "alertas_emitidas": (resumen.get("alertas") or {}).get("total_creadas", 0),
            "motivo_sin_predicciones": resumen.get("motivo"),
        }
    except Exception:
        if propio:
            db.rollback()
        raise
    finally:
        if propio:
            db.close()


def _fecha(valor: str) -> datetime:
    try:
        return datetime.fromisoformat(valor)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"Fecha ISO invalida: {valor!r}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Datos de demostracion (TASK-038).")
    parser.add_argument("--fecha", type=_fecha, default=None,
                        help="Fecha ISO de generacion; por defecto, ahora (UTC).")
    parser.add_argument("--forzar", action="store_true",
                        help="Agrega una nueva tanda de predicciones aunque ya existan.")
    parser.add_argument("--todos-los-municipios", action="store_true",
                        help="Antes de sembrar, amplia el catalogo a todos los municipios con "
                             "casos (app/etl/ampliar_catalogo.py, ADR-007). Sin esta opcion, "
                             "solo la zona piloto de 4 municipios.")
    args = parser.parse_args(argv)

    if args.todos_los_municipios:
        from app.etl import ampliar_catalogo  # importa pandas: solo si se pide
        ampliar_catalogo.main([])

    resultado = sembrar_demo(fecha_generacion=args.fecha, forzar=args.forzar)
    print(f"Usuarios demo: {resultado['usuarios']}")
    casos = resultado["casos"]
    if "omitida" in casos:
        print(f"Casos observados: omitidos ({casos['omitida']})")
    else:
        print(f"Casos observados: dengue {casos['dengue_semanal']['insertados']} filas semanales, "
              f"malaria {casos['malaria_acumulada']['insertados']} filas acumuladas")
    print(f"Modelo {resultado['modelo_id']} ({'registrado' if resultado['modelo_creado'] else 'ya existia'})")
    print(f"Predicciones insertadas: {resultado['predicciones_insertadas']}")
    if resultado["motivo_sin_predicciones"]:
        print(f"Sin predicciones nuevas: {resultado['motivo_sin_predicciones']}")
    if resultado["predicciones_omitidas"]:
        fuera = len(resultado["predicciones_omitidas"])
        print(f"Omitidas (municipios fuera del catalogo): {fuera}")
    print(f"Alertas emitidas con el umbral vigente: {resultado['alertas_emitidas']}")
    print("Malaria: sin predicciones (no hay modelo; ver ADR-005). Brotes confirmados: no se cargan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
