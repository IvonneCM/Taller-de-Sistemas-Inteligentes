"""Importa todos los modelos ORM para que Alembic (autogenerate) y
SQLAlchemy (resolucion de relationships por nombre de clase) los vean en un
solo lugar."""

from app.models.departamento import Departamento  # noqa: F401
from app.models.municipio import Municipio  # noqa: F401
from app.models.enfermedad import Enfermedad  # noqa: F401
from app.models.caso_epidemiologico import CasoEpidemiologico  # noqa: F401
from app.models.dato_climatico import DatoClimatico  # noqa: F401
from app.models.rol import Rol  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.modelo import Modelo  # noqa: F401
from app.models.prediccion import Prediccion  # noqa: F401
from app.models.alerta import Alerta  # noqa: F401
from app.models.umbral_configuracion import UmbralConfiguracion  # noqa: F401
from app.models.brote_confirmado import BroteConfirmado  # noqa: F401
from app.models.brote_simulado import BroteSimulado  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

__all__ = [
    "Departamento",
    "Municipio",
    "Enfermedad",
    "CasoEpidemiologico",
    "DatoClimatico",
    "Rol",
    "Usuario",
    "Modelo",
    "Prediccion",
    "Alerta",
    "UmbralConfiguracion",
    "BroteConfirmado",
    "RefreshToken",
]
