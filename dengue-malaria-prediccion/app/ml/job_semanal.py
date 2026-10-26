"""Job semanal de prediccion (TASK-016 / REQ-002, REQ-009).

    python -m app.ml.job_semanal [--fecha 2026-11-02] [--forzar]

Cada ejecucion hace lo mismo que el pipeline de `app/ml/prediccion.py`, de punta
a punta y sin pasos manuales:

  1. se asegura de que el modelo versionado este registrado en `modelos`;
  2. genera las predicciones de dengue a 3 semanas sobre el panel semanal;
  3. persiste las de los municipios del catalogo (solo INSERT, nunca UPDATE);
  4. evalua las alertas con el umbral vigente (TASK-015, REQ-010).

Es idempotente por SEMANA ISO: si el modelo ya generó predicciones esa semana
no agrega otra tanda (salvo `--forzar`), de modo que un reintento o una doble
ejecucion no duplica nada. Sale con codigo 0 si todo salio bien y 1 si fallo.

Limite que hay que decir en voz alta: la ingesta de boletines nuevos NO es
automatica. Mientras el panel no cambie, cada tanda semanal repite las mismas
probabilidades con una nueva fecha de generacion.

La programacion esta en `.github/workflows/prediccion_semanal.yml` (GitHub
Actions), porque el servicio web gratuito se duerme y no puede tener un cron.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.ml import entrenamiento, prediccion
from app.ml.features import cargar_features
from app.models import Modelo, Prediccion

logger = logging.getLogger(__name__)


def asegurar_modelo(db, version: str, directorio: Path) -> tuple[int, bool]:
    """Devuelve (modelo_id, creado). Registra el modelo si aun no esta en la base."""
    ruta = directorio / f"baseline_dengue_t{prediccion.HORIZONTE_PUBLICADO}_{version}_metadata.json"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}; entrenar con app.ml.entrenamiento.")
    metadata = json.loads(ruta.read_text(encoding="utf-8"))
    existente = db.execute(
        select(Modelo).where(Modelo.nombre == metadata["nombre"], Modelo.version == metadata["version"])
    ).scalars().first()
    if existente is not None:
        return existente.id, False
    return entrenamiento.registrar_metricas_bd(metadata, session=db), True


def inicio_de_semana_iso(momento: datetime) -> datetime:
    """Lunes 00:00 UTC de la semana ISO del momento dado."""
    utc = momento.astimezone(timezone.utc)
    lunes = utc.date() - timedelta(days=utc.weekday())
    return datetime(lunes.year, lunes.month, lunes.day, tzinfo=timezone.utc)


def ejecutar(
    db,
    *,
    fecha_generacion: datetime | date | None = None,
    version: str | None = None,
    forzar: bool = False,
    panel: Path | None = None,
    directorio: Path | None = None,
) -> dict:
    """Una pasada del job sobre la sesion dada (el que llama decide el commit)."""
    version = version or entrenamiento.MODEL_VERSION
    directorio = Path(directorio) if directorio else entrenamiento.ARTIFACTS_DIR
    momento = fecha_generacion
    if momento is None:
        momento = datetime.now(timezone.utc)
    elif not isinstance(momento, datetime):
        momento = datetime(momento.year, momento.month, momento.day, tzinfo=timezone.utc)
    elif momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    modelo_id, modelo_creado = asegurar_modelo(db, version, directorio)

    desde = inicio_de_semana_iso(momento)
    ya_esta_semana = db.scalar(
        select(func.count()).select_from(Prediccion).where(
            Prediccion.modelo_id == modelo_id,
            Prediccion.fecha_generacion >= desde,
            Prediccion.fecha_generacion < desde + timedelta(days=7),
        )
    )
    if ya_esta_semana and not forzar:
        logger.info("Semana %s: el modelo %s ya tiene %s predicciones; no se agrega otra tanda.",
                    desde.date().isoformat(), modelo_id, ya_esta_semana)
        return {"modelo_id": modelo_id, "modelo_creado": modelo_creado, "omitida": True,
                "motivo": f"ya hay predicciones de la semana ISO que empieza el {desde.date().isoformat()}",
                "insertadas": 0, "alertas": 0}

    resultado = cargar_features(panel) if panel is not None else cargar_features()
    calculadas = prediccion.generar_predicciones(
        resultado, horizonte=prediccion.HORIZONTE_PUBLICADO,
        fecha_generacion=momento, version=version, directorio=directorio,
    )
    resumen = prediccion.persistir_predicciones(
        calculadas, modelo_id=modelo_id, session=db, evaluar_alertas=True
    )
    alertas = (resumen.get("alertas") or {}).get("total_creadas", 0)
    logger.info("Job semanal: %s predicciones insertadas, %s alertas emitidas (modelo %s).",
                len(resumen["insertadas"]), alertas, modelo_id)
    return {"modelo_id": modelo_id, "modelo_creado": modelo_creado, "omitida": False,
            "insertadas": len(resumen["insertadas"]), "omitidas_fuera_del_catalogo": len(resumen["omitidas"]),
            "alertas": alertas, "fecha_generacion": momento.isoformat()}


def _fecha(valor: str) -> datetime:
    try:
        return datetime.fromisoformat(valor)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"Fecha ISO invalida: {valor!r}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Job semanal de prediccion (TASK-016).")
    parser.add_argument("--fecha", type=_fecha, default=None, help="Fecha ISO de generacion; por defecto, ahora (UTC).")
    parser.add_argument("--forzar", action="store_true", help="Agrega la tanda aunque ya haya una esta semana.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db = SessionLocal()
    try:
        resumen = ejecutar(db, fecha_generacion=args.fecha, forzar=args.forzar)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("El job semanal fallo; no se guardo nada.")
        return 1
    finally:
        db.close()

    if resumen["omitida"]:
        print(f"Sin cambios: {resumen['motivo']} (use --forzar para agregar otra tanda).")
    else:
        print(f"Predicciones insertadas: {resumen['insertadas']} · alertas emitidas: {resumen['alertas']} "
              f"· fecha de generacion: {resumen['fecha_generacion']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
