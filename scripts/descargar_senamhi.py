import os
import time
import requests
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "clima",
    "senamhi"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "senamhi_raw_SE01_13_2026.csv"
)

PARCIAL_FILE = os.path.join(
    OUTPUT_DIR,
    "senamhi_descarga_parcial.csv"
)

URL = (
    "https://wis.senamhi.gob.bo/oapi/collections/"
    "urn%3Awmo%3Amd%3Abo-senamhi%3A51lca7/items"
)


# ============================================================
# ESTACIONES
# ============================================================

ESTACIONES = {
    "0-68-0-810201111863": "GUAYARAMERIN",
    "0-68-0-200307011861": "IXIAMAS",
    "0-68-0-200310111860": "SAN BUENAVENTURA",
    "0-68-0-207003811866": "PALOS BLANCOS"
}


# ============================================================
# VARIABLES
# ============================================================

VARIABLES_VALIDAS = {
    "air_temperature",
    "relative_humidity",
    "total_precipitation_or_total_water_equivalent"
}


# ============================================================
# PERIODO
# ============================================================

FECHA_INICIO = pd.Timestamp(
    "2026-01-01T00:00:00Z"
)

FECHA_FIN = pd.Timestamp(
    "2026-04-04T23:59:59Z"
)


# ============================================================
# PRECIPITACIÓN 24 HORAS
# ============================================================

def es_precipitacion_24h(phenomenon_time):

    if not phenomenon_time:
        return False

    if "/" not in phenomenon_time:
        return False

    try:

        inicio, fin = phenomenon_time.split("/")

        inicio = pd.to_datetime(inicio)
        fin = pd.to_datetime(fin)

        duracion = fin - inicio

        return duracion == pd.Timedelta(hours=24)

    except Exception:

        return False


# ============================================================
# PROCESAR OBSERVACIÓN
# ============================================================

def procesar_feature(feature):

    propiedades = feature.get(
        "properties",
        {}
    )

    variable = propiedades.get("name")

    if variable not in VARIABLES_VALIDAS:
        return None


    wigos = propiedades.get(
        "wigos_station_identifier"
    )

    if wigos not in ESTACIONES:
        return None


    fecha = propiedades.get("reportTime")

    if not fecha:
        return None


    try:
        fecha = pd.to_datetime(fecha)
    except Exception:
        return None


    if fecha < FECHA_INICIO:
        return None

    if fecha > FECHA_FIN:
        return None


    # --------------------------------------------------------
    # PRECIPITACIÓN
    # --------------------------------------------------------

    if (
        variable
        == "total_precipitation_or_total_water_equivalent"
    ):

        phenomenon_time = propiedades.get(
            "phenomenonTime"
        )

        if not es_precipitacion_24h(
            phenomenon_time
        ):
            return None


    # --------------------------------------------------------
    # COORDENADAS
    # --------------------------------------------------------

    geometria = feature.get(
        "geometry"
    ) or {}

    coordenadas = geometria.get(
        "coordinates"
    ) or []


    longitud = None
    latitud = None

    if len(coordenadas) >= 2:

        longitud = coordenadas[0]
        latitud = coordenadas[1]


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {

        "fecha_hora":
            fecha.isoformat(),

        "municipio":
            ESTACIONES[wigos],

        "wigos_id":
            wigos,

        "variable":
            variable,

        "valor":
            propiedades.get("value"),

        "unidad":
            propiedades.get("units"),

        "phenomenon_time":
            propiedades.get("phenomenonTime"),

        "latitud":
            latitud,

        "longitud":
            longitud,

        "fuente":
            "SENAMHI Bolivia - WIS 2.0"
    }


# ============================================================
# GUARDAR PROGRESO
# ============================================================

def guardar_parcial(filas):

    if not filas:
        return

    df = pd.DataFrame(filas)

    df = df.drop_duplicates()

    df.to_csv(
        PARCIAL_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# PETICIÓN CON REINTENTOS
# ============================================================

def solicitar_pagina(parametros):

    MAX_INTENTOS = 5

    for intento in range(
        1,
        MAX_INTENTOS + 1
    ):

        try:

            respuesta = requests.get(
                URL,
                params=parametros,

                # tiempo de conexión,
                # tiempo máximo de lectura
                timeout=(15, 120)
            )

            respuesta.raise_for_status()

            return respuesta.json()


        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ) as error:

            print(
                f"⚠ Problema de conexión "
                f"(intento {intento}/{MAX_INTENTOS})"
            )

            print(
                type(error).__name__
            )


            if intento == MAX_INTENTOS:

                raise


            # Espera progresiva:
            # 10, 20, 30, 40 segundos

            espera = intento * 10

            print(
                f"Esperando {espera} segundos..."
            )

            time.sleep(espera)


        except requests.exceptions.HTTPError as error:

            print(
                "⚠ Error HTTP:",
                error
            )

            raise


# ============================================================
# DESCARGA
# ============================================================

def descargar():

    print(
        "\n======================================"
    )

    print(
        "DESCARGA SENAMHI WIS 2.0"
    )

    print(
        "======================================"
    )

    print(
        "Periodo: SE 1-13 de 2026"
    )

    print(
        "Estaciones seleccionadas:",
        len(ESTACIONES)
    )


    filas = []

    offset = 0

    limit = 1000

    pagina = 1


    while True:

        print(
            f"\nDescargando página {pagina} "
            f"(offset {offset})..."
        )


        parametros = {

            "f": "json",

            "limit": limit,

            "offset": offset
        }


        try:

            datos = solicitar_pagina(
                parametros
            )


        except Exception as error:

            print(
                "\n❌ No fue posible continuar "
                "después de varios intentos."
            )

            print(
                "Último error:",
                error
            )

            print(
                "\nGuardando todo el progreso..."
            )

            guardar_parcial(filas)

            print(
                "Progreso guardado en:"
            )

            print(
                PARCIAL_FILE
            )

            return pd.DataFrame(filas)


        features = datos.get(
            "features",
            []
        )


        if not features:

            print(
                "\nNo existen más registros."
            )

            break


        nuevos = 0


        for feature in features:

            fila = procesar_feature(
                feature
            )

            if fila is not None:

                filas.append(
                    fila
                )

                nuevos += 1


        print(
            "Registros útiles de esta página:",
            nuevos
        )

        print(
            "Registros útiles acumulados:",
            len(filas)
        )


        # ----------------------------------------------------
        # GUARDADO PERIÓDICO
        # ----------------------------------------------------

        # Cada 5 páginas guardamos lo encontrado.

        if pagina % 5 == 0:

            guardar_parcial(
                filas
            )

            print(
                "✓ Progreso guardado."
            )


        # ----------------------------------------------------
        # VERIFICAR SIGUIENTE PÁGINA
        # ----------------------------------------------------

        links = datos.get(
            "links",
            []
        )


        existe_next = any(

            link.get("rel") == "next"

            for link in links
        )


        if not existe_next:

            print(
                "\nLa API indica que no "
                "hay más páginas."
            )

            break


        offset += limit

        pagina += 1


    # Guardado final parcial

    guardar_parcial(
        filas
    )


    return pd.DataFrame(
        filas
    )


# ============================================================
# RESUMEN
# ============================================================

def mostrar_resumen(df):

    print(
        "\n======================================"
    )

    print(
        "RESUMEN DE LA DESCARGA"
    )

    print(
        "======================================"
    )


    print(
        "\nRegistros:",
        len(df)
    )


    print(
        "\nRegistros por municipio:"
    )

    print(
        df["municipio"]
        .value_counts()
    )


    print(
        "\nRegistros por variable:"
    )

    print(
        df["variable"]
        .value_counts()
    )


    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"]
    )


    print(
        "\nCobertura temporal:"
    )

    print(
        "Desde:",
        df["fecha_hora"].min()
    )

    print(
        "Hasta:",
        df["fecha_hora"].max()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    df = descargar()


    if df.empty:

        print(
            "\n❌ No se obtuvieron "
            "observaciones."
        )

        return


    # --------------------------------------------------------
    # LIMPIEZA DE DUPLICADOS
    # --------------------------------------------------------

    cantidad_original = len(df)

    df = df.drop_duplicates()

    eliminados = (
        cantidad_original
        - len(df)
    )


    print(
        "\nDuplicados exactos eliminados:",
        eliminados
    )


    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    df["fecha_hora"] = pd.to_datetime(
        df["fecha_hora"]
    )


    df = df.sort_values(
        [
            "municipio",
            "fecha_hora",
            "variable"
        ]
    )


    # --------------------------------------------------------
    # GUARDAR CSV DEFINITIVO
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


    mostrar_resumen(
        df
    )


    print(
        "\n======================================"
    )

    print(
        "✓ DESCARGA FINALIZADA"
    )

    print(
        "======================================"
    )

    print(
        "\nArchivo:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()