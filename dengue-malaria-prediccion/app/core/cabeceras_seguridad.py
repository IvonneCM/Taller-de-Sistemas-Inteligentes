"""Cabeceras de seguridad de la API (TASK-035, hallazgos H-4 y H-9, NFR-005).

Se agregan a TODAS las respuestas, incluidos los errores. En produccion ademas se
envia `Strict-Transport-Security` (Render sirve la API solo por HTTPS) y una CSP
cerrada: en produccion no se publica /docs ni /redoc (TASK-035), asi que no hace
falta cargar nada desde otros origenes. En desarrollo se omiten esas dos para no
romper la documentacion interactiva ni forzar HTTPS en localhost.
"""

from fastapi import FastAPI, Request

from app.core.config import get_settings

BASE = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}
SOLO_PRODUCCION = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


def instalar(app: FastAPI) -> None:
    produccion = get_settings().ENVIRONMENT.lower() == "production"
    cabeceras = {**BASE, **(SOLO_PRODUCCION if produccion else {})}

    @app.middleware("http")
    async def agregar_cabeceras_de_seguridad(request: Request, call_next):
        respuesta = await call_next(request)
        for nombre, valor in cabeceras.items():
            respuesta.headers[nombre] = valor
        # Las respuestas de autenticacion llevan tokens: que nadie las guarde.
        if request.url.path.startswith("/auth/"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta
