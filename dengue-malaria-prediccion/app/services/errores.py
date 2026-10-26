"""Errores de dominio de la capa de servicio; las rutas los traducen a HTTP."""


class RecursoNoEncontrado(LookupError):
    """La zona, enfermedad o departamento pedido no existe."""
