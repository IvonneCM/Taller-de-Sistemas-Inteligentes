"""
Carga el catalogo base (departamentos, enfermedades, municipios piloto)
necesario para que los conectores de ingesta (TASK-008/009) y el pipeline
de limpieza (TASK-010) tengan claves foraneas validas contra las que
insertar.

No es una tarea numerada de tasks.md por si misma, pero es un prerequisito
tecnico de TASK-008/009/010: esos conectores insertan en
`casos_epidemiologicos` / `datos_climaticos`, que exigen `municipio_id` y
`enfermedad_id` ya existentes (NOT NULL FK).

Zona piloto: los 4 municipios confirmados en el reparto del equipo
(Guayaramerin, Ixiamas, Palos Blancos, San Buenaventura — ver design.md §10
y CONTEXT.md), los unicos con cruce real de datos climaticos +
epidemiologicos.

IMPORTANTE sobre la geometria (REQ-006 exige MULTIPOLYGON NOT NULL):
no se dispone todavia del poligono administrativo oficial (INE) de estos
municipios. Para no fabricar un limite territorial que no esta verificado
(ver CLAUDE.md regla 1), se usa un cuadrado pequeno (~0.05 grados, ~5 km de
lado) centrado en la coordenada real de la estacion SENAMHI de cada
municipio (ver data/processed/control_calidad_clima.csv), marcado
explicitamente como REFERENCIAL. Debe reemplazarse por el poligono oficial
del INE en una tarea posterior antes de usar este dato para calcular areas,
distancias entre limites o cualquier metrica que dependa de la forma real
del municipio.
"""

from app.core.database import SessionLocal
from app.models import Departamento, Enfermedad, Municipio

# (nombre, departamento, lat_estacion, lon_estacion) — coordenadas reales de
# la estacion SENAMHI usada como centro del buffer referencial, tomadas de
# data/processed/control_calidad_clima.csv.
MUNICIPIOS_PILOTO = [
    ("GUAYARAMERIN", "Beni", -10.83391, -65.34004),
    ("IXIAMAS", "La Paz", -13.77117, -68.13529),
    ("PALOS BLANCOS", "La Paz", -15.56095, -67.29962),
    ("SAN BUENAVENTURA", "La Paz", -14.43451, -67.54277),
]

ENFERMEDADES = ["dengue", "malaria"]

MEDIO_LADO_GRADOS = 0.025  # ~2.5 km desde el centro -> cuadrado de ~5 km de lado


def _buffer_wkt(lat: float, lon: float, medio_lado: float = MEDIO_LADO_GRADOS) -> str:
    """Cuadrado referencial centrado en (lat, lon), como WKT MULTIPOLYGON."""
    x0, x1 = lon - medio_lado, lon + medio_lado
    y0, y1 = lat - medio_lado, lat + medio_lado
    anillo = f"{x0} {y0}, {x1} {y0}, {x1} {y1}, {x0} {y1}, {x0} {y0}"
    return f"MULTIPOLYGON((({anillo})))"


def seed(db=None):
    """Idempotente: si el catalogo ya existe, no duplica filas."""
    propio = db is None
    if propio:
        db = SessionLocal()

    try:
        departamentos = {}
        for _, dep_nombre, _, _ in MUNICIPIOS_PILOTO:
            if dep_nombre in departamentos:
                continue
            existente = (
                db.query(Departamento).filter_by(nombre=dep_nombre).first()
            )
            departamentos[dep_nombre] = existente or Departamento(nombre=dep_nombre)
            if existente is None:
                db.add(departamentos[dep_nombre])
        db.flush()

        enfermedades = {}
        for nombre in ENFERMEDADES:
            existente = db.query(Enfermedad).filter_by(nombre=nombre).first()
            enfermedades[nombre] = existente or Enfermedad(nombre=nombre)
            if existente is None:
                db.add(enfermedades[nombre])
        db.flush()

        municipios = {}
        for nombre, dep_nombre, lat, lon in MUNICIPIOS_PILOTO:
            existente = db.query(Municipio).filter_by(nombre=nombre).first()
            if existente is None:
                existente = Municipio(
                    nombre=nombre,
                    departamento_id=departamentos[dep_nombre].id,
                    geometria=_buffer_wkt(lat, lon),
                    poblacion_estimada=None,
                )
                db.add(existente)
            municipios[nombre] = existente
        db.flush()

        if propio:
            db.commit()

        return {
            "departamentos": departamentos,
            "enfermedades": enfermedades,
            "municipios": municipios,
        }
    finally:
        if propio:
            db.close()


if __name__ == "__main__":
    resultado = seed()
    print("Catalogo cargado:")
    print(" Departamentos:", list(resultado["departamentos"].keys()))
    print(" Enfermedades:", list(resultado["enfermedades"].keys()))
    print(" Municipios:", list(resultado["municipios"].keys()))
