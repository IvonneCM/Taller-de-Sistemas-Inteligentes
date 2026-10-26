"""TASK-014 / REQ-001..003, NFR-007: pipeline de prediccion semanal.

Ejecuta features -> modelo XGBoost -> SHAP y calcula los campos persistibles
en `predicciones` (design.md §3):

- `nivel_riesgo`: cortes provisionales, NO validados empiricamente.
- `probabilidad_pct`: probabilidad del modelo de al menos un caso en t+h.
- `nivel_confianza`: derivado del porcentaje de faltantes/imputados de la
  ventana climatica. Se reutilizan los umbrales de `app.etl.limpieza`:
  <=5 % alto, >5 % y <=20 % bajo, >20 % no se publica. `medio` queda
  reservado y no se emite en esta version.
- `fecha_estimada_riesgo`: fecha de generacion + 21 (t+3) o 28 (t+4) dias.
- `variables_explicativas`: ranking SHAP local (log-odds) de TASK-013.

Horizonte operativo por defecto: t+3. El artefacto t+4 existe y puede usarse
explicitamente, pero no se publica en el lote semanal mientras la validacion
tenga solo dos origenes walk-forward y el esquema de `predicciones` no
distinga el horizonte de forma nativa.

El modulo no reentrena. La division cronologica del entrenamiento vive en
`app.ml.entrenamiento` (walk-forward por `fecha_semana`), no aqui. Tampoco
accede a la base de datos salvo en `persistir_predicciones`.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from numbers import Real
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from app.etl.limpieza import nivel_confianza as nivel_confianza_calidad
from app.ml.features import ResultadoFeatures, cargar_features

HORIZONTES = (3, 4)
HORIZONTE_PUBLICADO = 3
DIAS_POR_SEMANA = 7

# Cortes provisionales solicitados para TASK-014. No provienen de una
# validacion empirica ni de una definicion epidemiologica de brote.
UMBRAL_RIESGO_BAJO_PCT = 33.33
UMBRAL_RIESGO_MEDIO_PCT = 66.67

# NFR-007 / design.md §5, via app.etl.limpieza. `medio` queda reservado.
_CONFIANZA_A_NIVEL = {
    "confianza_normal": "alto",
    "confianza_baja": "bajo",
}
_MOTIVO_DATOS_INSUFICIENTES = "datos_insuficientes"
_MOTIVO_SIN_FEATURES = "sin_features"

_PREFIJOS_CLIMA = (
    "temperatura_media",
    "humedad_media",
    "precipitacion_total_mm",
)


@dataclass(frozen=True)
class PrediccionCalculada:
    """Resultado en memoria; no es una fila ORM ni se persiste por si solo."""

    municipio: str
    enfermedad: str
    horizonte_semanas: int
    fecha_generacion: datetime
    fecha_estimada_riesgo: date
    probabilidad_pct: float | None
    nivel_riesgo: str | None
    nivel_confianza: str | None
    variables_explicativas: tuple[dict, ...]
    publicada: bool
    motivo_no_publicacion: str | None = None


def _validar_horizonte(horizonte: int) -> int:
    if (
        isinstance(horizonte, bool)
        or not isinstance(horizonte, int)
        or horizonte not in HORIZONTES
    ):
        raise ValueError("El horizonte debe ser el entero 3 o 4.")
    return horizonte


def validar_porcentaje_faltante(porcentaje: float) -> float:
    """Valida un porcentaje de faltantes/imputados en el rango 0-100."""
    try:
        valor = float(porcentaje)
    except (TypeError, ValueError) as exc:
        raise ValueError("El porcentaje de faltantes debe ser numerico.") from exc
    if not math.isfinite(valor) or not 0.0 <= valor <= 100.0:
        raise ValueError("El porcentaje de faltantes debe estar entre 0 y 100.")
    return valor


def clasificar_nivel_riesgo(probabilidad_pct: float) -> str:
    """Cortes provisionales: <33.33 bajo, <66.67 medio, >=66.67 alto."""
    try:
        valor = float(probabilidad_pct)
    except (TypeError, ValueError) as exc:
        raise ValueError("La probabilidad debe ser numerica.") from exc
    if not math.isfinite(valor) or not 0.0 <= valor <= 100.0:
        raise ValueError("La probabilidad debe estar entre 0 y 100.")
    if valor < UMBRAL_RIESGO_BAJO_PCT:
        return "bajo"
    if valor < UMBRAL_RIESGO_MEDIO_PCT:
        return "medio"
    return "alto"


def clasificar_nivel_confianza(porcentaje_faltante: float) -> str | None:
    """Traduce NFR-007 a `nivel_confianza`; None significa no publicar."""
    porcentaje = validar_porcentaje_faltante(porcentaje_faltante)
    calidad = nivel_confianza_calidad(porcentaje)
    return _CONFIANZA_A_NIVEL.get(calidad)


def normalizar_fecha_generacion(
    fecha_generacion: datetime | date | None,
) -> datetime:
    """Devuelve un datetime UTC; una fecha suelta se interpreta a medianoche."""
    if fecha_generacion is None:
        return datetime.now(timezone.utc)
    if isinstance(fecha_generacion, datetime):
        if fecha_generacion.tzinfo is None:
            return fecha_generacion.replace(tzinfo=timezone.utc)
        return fecha_generacion.astimezone(timezone.utc)
    if isinstance(fecha_generacion, date):
        return datetime.combine(
            fecha_generacion, time.min, tzinfo=timezone.utc
        )
    raise TypeError("fecha_generacion debe ser date, datetime o None.")


def calcular_fecha_estimada_riesgo(
    fecha_generacion: datetime | date | None, horizonte: int
) -> date:
    """fecha_generacion + 21 dias (t+3) o + 28 dias (t+4)."""
    horizonte = _validar_horizonte(horizonte)
    generacion = normalizar_fecha_generacion(fecha_generacion)
    return generacion.date() + timedelta(
        days=horizonte * DIAS_POR_SEMANA
    )


def columnas_climaticas(columnas: Sequence[str]) -> list[str]:
    """Selecciona las features climaticas generadas por TASK-011."""
    return [c for c in columnas if c.startswith(_PREFIJOS_CLIMA)]


def estimar_porcentaje_faltante_climatico(
    fila: pd.Series, columnas: Sequence[str] | None = None
) -> float:
    """Proporcion de features climaticas ausentes en la ventana de la fila.

    Es una aproximacion cuando el llamador no entrega el porcentaje real de
    TASK-010. No detecta valores ya imputados: el panel v2 de NASA POWER no
    conserva `es_dato_imputado`. Para produccion debe pasarse el porcentaje
    de `clima_semanal_calidad.csv` o del modulo de limpieza.
    """
    seleccion = list(columnas) if columnas is not None else columnas_climaticas(
        list(fila.index)
    )
    if not seleccion:
        raise ValueError("No hay columnas climaticas para estimar faltantes.")
    return round(float(pd.isna(fila[seleccion]).mean() * 100.0), 2)


def _ultimas_filas(resultado: ResultadoFeatures) -> list:
    indices: list = []
    for _, grupo in resultado.claves.groupby(
        ["municipio", "enfermedad"], sort=False
    ):
        indices.append(grupo["fecha_semana"].idxmax())
    return indices


def _resolver_porcentajes(
    porcentajes: float | pd.Series | Mapping | None,
    indices: Sequence,
    resultado: ResultadoFeatures,
    columnas_clima: Sequence[str],
) -> dict:
    if porcentajes is None:
        return {
            indice: estimar_porcentaje_faltante_climatico(
                resultado.features.loc[indice], columnas_clima
            )
            for indice in indices
        }
    if isinstance(porcentajes, Real) and not isinstance(porcentajes, bool):
        valor = validar_porcentaje_faltante(float(porcentajes))
        return {indice: valor for indice in indices}
    if isinstance(porcentajes, pd.Series):
        faltantes = [indice for indice in indices if indice not in porcentajes.index]
        if faltantes:
            raise ValueError(
                "Faltan porcentajes para indices: "
                f"{faltantes[:5]}{'...' if len(faltantes) > 5 else ''}."
            )
        return {
            indice: validar_porcentaje_faltante(porcentajes.loc[indice])
            for indice in indices
        }
    if isinstance(porcentajes, Mapping):
        faltantes = [indice for indice in indices if indice not in porcentajes]
        if faltantes:
            raise ValueError(
                "Faltan porcentajes para indices: "
                f"{faltantes[:5]}{'...' if len(faltantes) > 5 else ''}."
            )
        return {
            indice: validar_porcentaje_faltante(porcentajes[indice])
            for indice in indices
        }
    raise TypeError(
        "porcentajes_faltantes debe ser None, un numero, una Series o un dict."
    )


def _cargar_artefacto(horizonte: int, version: str | None, directorio: Path | None):
    from app.ml.entrenamiento import MODEL_VERSION, cargar_artefacto

    version_final = version or MODEL_VERSION
    if directorio is None:
        return cargar_artefacto(horizonte, version=version_final)
    return cargar_artefacto(
        horizonte, version=version_final, directorio=Path(directorio)
    )


def _explicar_por_defecto(
    datos: pd.DataFrame, horizonte: int, directorio: Path | None
) -> list[dict]:
    from app.ml.explicabilidad import explicar_observaciones

    return explicar_observaciones(
        datos, horizonte, directorio=directorio
    )


def generar_predicciones(
    resultado: ResultadoFeatures,
    *,
    horizonte: int = HORIZONTE_PUBLICADO,
    fecha_generacion: datetime | date | None = None,
    porcentajes_faltantes: float | pd.Series | Mapping | None = None,
    version: str | None = None,
    directorio: Path | None = None,
    explicador: Callable[[pd.DataFrame, int], list[dict]] | None = None,
    solo_ultima_semana: bool = True,
) -> list[PrediccionCalculada]:
    """Genera predicciones completas para una o todas las filas del panel.

    `explicador` permite inyectar TASK-013 en pruebas; por defecto se usa
    `app.ml.explicabilidad.explicar_observaciones`.
    """
    horizonte = _validar_horizonte(horizonte)
    generacion = normalizar_fecha_generacion(fecha_generacion)
    artefacto = _cargar_artefacto(horizonte, version, directorio)

    faltantes = [c for c in artefacto.features if c not in resultado.features]
    if faltantes:
        raise ValueError(f"Faltan features del artefacto: {faltantes}")

    indices = _ultimas_filas(resultado) if solo_ultima_semana else list(
        resultado.features.index
    )
    if not indices:
        raise ValueError("El panel no contiene filas para predecir.")

    X = resultado.features.loc[indices, artefacto.features]
    columnas_clima = columnas_climaticas(artefacto.features)
    porcentajes = _resolver_porcentajes(
        porcentajes_faltantes, indices, resultado, columnas_clima
    )

    from app.ml.entrenamiento import predecir_probabilidad

    probabilidades = np.asarray(predecir_probabilidad(artefacto, X), dtype=float)
    if probabilidades.shape != (len(indices),):
        raise RuntimeError("El modelo devolvio una forma de probabilidades inesperada.")

    sin_features = [bool(X.iloc[pos].isna().all()) for pos in range(len(indices))]
    niveles_confianza = [
        clasificar_nivel_confianza(porcentajes[indice])
        if not sin_features[pos]
        else None
        for pos, indice in enumerate(indices)
    ]
    publicables = [
        not sin_features[pos] and niveles_confianza[pos] is not None
        for pos in range(len(indices))
    ]

    explicaciones: list[list[dict] | None] = [None] * len(indices)
    if any(publicables):
        funcion = explicador or (
            lambda datos, h: _explicar_por_defecto(datos, h, directorio)
        )
        salidas = funcion(X.loc[publicables], horizonte)
        if len(salidas) != sum(publicables):
            raise RuntimeError("SHAP devolvio un numero de explicaciones distinto.")
        for pos, salida in zip(
            [i for i, ok in enumerate(publicables) if ok], salidas
        ):
            ranking = salida.get("explicaciones", [])
            if not ranking:
                raise RuntimeError("SHAP devolvio una explicacion vacia.")
            explicaciones[pos] = [
                {
                    "variable": str(item["variable"]),
                    "peso": float(item["peso"]),
                }
                for item in ranking
            ]

    predicciones: list[PrediccionCalculada] = []
    for pos, indice in enumerate(indices):
        clave = resultado.claves.loc[indice]
        probabilidad_pct = (
            None if sin_features[pos] else round(float(probabilidades[pos]) * 100.0, 2)
        )
        nivel_riesgo = (
            clasificar_nivel_riesgo(probabilidad_pct)
            if probabilidad_pct is not None
            else None
        )
        nivel_confianza = niveles_confianza[pos]
        if sin_features[pos]:
            motivo = _MOTIVO_SIN_FEATURES
        elif nivel_confianza is None:
            motivo = _MOTIVO_DATOS_INSUFICIENTES
        else:
            motivo = None
        predicciones.append(
            PrediccionCalculada(
                municipio=str(clave["municipio"]),
                enfermedad=str(clave["enfermedad"]),
                horizonte_semanas=horizonte,
                fecha_generacion=generacion,
                fecha_estimada_riesgo=calcular_fecha_estimada_riesgo(
                    generacion, horizonte
                ),
                probabilidad_pct=probabilidad_pct,
                nivel_riesgo=nivel_riesgo,
                nivel_confianza=nivel_confianza,
                variables_explicativas=tuple(explicaciones[pos] or ()),
                publicada=motivo is None,
                motivo_no_publicacion=motivo,
            )
        )
    return predicciones


def construir_fila_orm(
    prediccion: PrediccionCalculada,
    *,
    municipio_id: int,
    enfermedad_id: int,
    modelo_id: int,
):
    """Construye la fila `predicciones` validando design.md §3 antes del INSERT."""
    from app.models.prediccion import Prediccion as PrediccionORM

    if not prediccion.publicada:
        raise ValueError("No se persiste una prediccion no publicada.")
    if prediccion.probabilidad_pct is None or prediccion.nivel_riesgo is None:
        raise ValueError("La prediccion publicada debe tener probabilidad y riesgo.")
    if prediccion.nivel_confianza is None:
        raise ValueError("La prediccion publicada debe tener nivel de confianza.")
    if not prediccion.variables_explicativas:
        raise ValueError(
            "La prediccion publicada debe tener variables explicativas (REQ-004)."
        )
    dias = (
        prediccion.fecha_estimada_riesgo
        - prediccion.fecha_generacion.date()
    ).days
    if not 21 <= dias <= 28:
        raise ValueError("El horizonte persistido debe estar entre 21 y 28 dias.")

    return PrediccionORM(
        municipio_id=municipio_id,
        enfermedad_id=enfermedad_id,
        modelo_id=modelo_id,
        fecha_generacion=prediccion.fecha_generacion,
        fecha_estimada_riesgo=prediccion.fecha_estimada_riesgo,
        nivel_riesgo=prediccion.nivel_riesgo,
        probabilidad_pct=prediccion.probabilidad_pct,
        nivel_confianza=prediccion.nivel_confianza,
        variables_explicativas=list(prediccion.variables_explicativas),
    )


def persistir_predicciones(
    predicciones: Sequence[PrediccionCalculada],
    *,
    modelo_id: int,
    session=None,
    evaluar_alertas: bool = False,
) -> dict:
    """Inserta solo predicciones publicadas; nunca actualiza filas existentes.

    Municipios o enfermedades fuera del catalogo se omiten con un motivo
    explicito. Si `session` es None se abre y cierra una sesion propia.
    Si `evaluar_alertas` es True (TASK-015), evalua los umbrales e inserta
    alertas justificadas para las predicciones persistidas.
    """
    from app.core.database import SessionLocal
    from app.models import Enfermedad, Modelo, Municipio

    propia = session is None
    if propia:
        session = SessionLocal()
    try:
        if session.get(Modelo, modelo_id) is None:
            raise ValueError(f"No existe el modelo_id {modelo_id}.")
        municipios = {
            fila.nombre.strip().casefold(): fila
            for fila in session.query(Municipio).all()
        }
        enfermedades = {
            fila.nombre.strip().casefold(): fila
            for fila in session.query(Enfermedad).all()
        }

        insertadas: list[int] = []
        omitidas: list[dict] = []
        no_publicadas = 0
        for prediccion in predicciones:
            if not prediccion.publicada:
                no_publicadas += 1
                continue
            municipio = municipios.get(prediccion.municipio.strip().casefold())
            if municipio is None:
                omitidas.append(
                    {
                        "municipio": prediccion.municipio,
                        "motivo": "municipio_no_en_catalogo",
                    }
                )
                continue
            enfermedad = enfermedades.get(prediccion.enfermedad.strip().casefold())
            if enfermedad is None:
                omitidas.append(
                    {
                        "municipio": prediccion.municipio,
                        "motivo": "enfermedad_no_en_catalogo",
                    }
                )
                continue
            fila = construir_fila_orm(
                prediccion,
                municipio_id=municipio.id,
                enfermedad_id=enfermedad.id,
                modelo_id=modelo_id,
            )
            session.add(fila)
            session.flush()
            insertadas.append(int(fila.id))

        resumen_alertas = None
        if evaluar_alertas and insertadas:
            from app.ml.evaluacion_alertas import evaluar_alertas_lote

            resumen_alertas = evaluar_alertas_lote(
                session, insertadas, commit=False
            )

        if propia:
            session.commit()
        return {
            "insertadas": insertadas,
            "omitidas": omitidas,
            "no_publicadas": no_publicadas,
            "alertas": resumen_alertas,
        }
    finally:
        if propia:
            session.close()


def _parse_fecha(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        if "T" in valor or " " in valor:
            return datetime.fromisoformat(valor.replace("Z", "+00:00"))
        return datetime.combine(date.fromisoformat(valor), time.min)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Fecha invalida; usar ISO 8601 (ej. 2026-03-30 o 2026-03-30T12:00:00Z)."
        ) from exc


def _imprimir_resumen(
    predicciones: Sequence[PrediccionCalculada], resumen: dict | None
) -> None:
    publicadas = [p for p in predicciones if p.publicada]
    print(
        f"Predicciones generadas: {len(predicciones)} "
        f"(publicadas={len(publicadas)}, "
        f"no_publicadas={len(predicciones) - len(publicadas)})"
    )
    for nivel in ("alto", "medio", "bajo"):
        cantidad = sum(1 for p in publicadas if p.nivel_riesgo == nivel)
        print(f"  nivel_riesgo={nivel}: {cantidad}")
    if resumen is not None:
        print(
            f"Persistidas: {len(resumen['insertadas'])}; "
            f"omitidas: {len(resumen['omitidas'])}; "
            f"no_publicadas: {resumen['no_publicadas']}"
        )
        if resumen.get("alertas"):
            al = resumen["alertas"]
            print(
                f"Alertas emitidas: {al.get('total_creadas', 0)}; "
                f"omitidas sin explicacion (REQ-005): {len(al.get('omitidas_sin_explicacion', []))}"
            )
        if resumen["omitidas"]:
            print(f"  primeras omisiones: {resumen['omitidas'][:5]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera predicciones semanales de dengue (TASK-014)."
    )
    parser.add_argument(
        "--horizonte",
        type=int,
        choices=list(HORIZONTES),
        default=HORIZONTE_PUBLICADO,
        help="Horizonte en semanas. Por defecto 3 (operativo).",
    )
    parser.add_argument(
        "--fecha-generacion",
        type=lambda v: _parse_fecha(v),
        default=None,
        help="Fecha ISO de generacion. Por defecto, ahora en UTC.",
    )
    parser.add_argument("--panel", type=Path, default=None)
    parser.add_argument("--version", type=str, default=None)
    parser.add_argument(
        "--modelo-id",
        type=int,
        default=None,
        help="Si se indica, persiste en predicciones (requiere DATABASE_URL).",
    )
    parser.add_argument(
        "--todas-las-semanas",
        action="store_true",
        help="Predice todas las filas del panel, no solo la ultima por municipio.",
    )
    parser.add_argument(
        "--porcentaje-faltante",
        type=float,
        default=None,
        help="Porcentaje global de faltantes/imputados (NFR-007).",
    )
    parser.add_argument(
        "--no-alertas",
        dest="evaluar_alertas",
        action="store_false",
        default=True,
        help="Omite la evaluacion automatica de alertas al persistir.",
    )
    args = parser.parse_args(argv)

    resultado = (
        cargar_features(args.panel)
        if args.panel is not None
        else cargar_features()
    )
    predicciones = generar_predicciones(
        resultado,
        horizonte=args.horizonte,
        fecha_generacion=args.fecha_generacion,
        porcentajes_faltantes=args.porcentaje_faltante,
        version=args.version,
        solo_ultima_semana=not args.todas_las_semanas,
    )
    resumen = None
    if args.modelo_id is not None:
        resumen = persistir_predicciones(
            predicciones,
            modelo_id=args.modelo_id,
            evaluar_alertas=args.evaluar_alertas,
        )
    _imprimir_resumen(predicciones, resumen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
