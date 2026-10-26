"""Logs con identificador de peticion y manejo uniforme de errores
(TASK-040 / NFR-003).

- Cada peticion recibe un `X-Request-ID` (el del cliente si es valido, si no
  uno nuevo) que aparece en la respuesta y en todos los logs de esa peticion.
- Una base de datos caida o lenta responde 503 (reintentable), no 500.
- Cualquier error no previsto responde 500 con un mensaje generico y el
  `request_id`: la traza queda en el log del servidor, nunca en la respuesta.
- Los errores de validacion (422) no devuelven el valor enviado (`input`),
  porque podria ser una contrasena.
- No se registran cuerpos, cabeceras ni cadenas de consulta: solo metodo, ruta,
  estado y duracion (REQ-020, NFR-005).
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = logging.getLogger("app.http")

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_FORMATO_LOG = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
_MARCA_HANDLER = "_observabilidad_handler"


class _FiltroRequestId(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configura el log raiz una sola vez (idempotente)."""
    raiz = logging.getLogger()
    nivel = logging.getLevelName(level.upper())
    raiz.setLevel(nivel if isinstance(nivel, int) else logging.INFO)
    if any(getattr(h, _MARCA_HANDLER, False) for h in raiz.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMATO_LOG))
    handler.addFilter(_FiltroRequestId())
    setattr(handler, _MARCA_HANDLER, True)
    raiz.addHandler(handler)


def _respuesta_error(
    estado: int, detalle: str, request_id: str, cabeceras: dict | None = None
) -> JSONResponse:
    respuesta = JSONResponse(
        status_code=estado,
        content={"detail": detalle, "request_id": request_id},
        headers=cabeceras,
    )
    respuesta.headers["X-Request-ID"] = request_id
    return respuesta


def instalar(app: FastAPI) -> None:
    """Registra el middleware de peticion y los manejadores de errores."""

    @app.middleware("http")
    async def middleware_peticion(request: Request, call_next):
        entrante = request.headers.get("x-request-id", "")
        request_id = entrante if _REQUEST_ID_VALIDO.match(entrante) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        inicio = time.perf_counter()
        try:
            try:
                respuesta = await call_next(request)
            except Exception:
                # Lo no previsto: traza al log (con request_id), nada al cliente.
                logger.exception("Error no controlado en %s %s", request.method, request.url.path)
                respuesta = _respuesta_error(
                    500, "Error interno del servidor.", request_id
                )
            milisegundos = (time.perf_counter() - inicio) * 1000
            nivel = (
                logging.ERROR if respuesta.status_code >= 500
                else logging.WARNING if respuesta.status_code >= 400
                else logging.INFO
            )
            logger.log(
                nivel, "%s %s -> %s (%.0f ms)",
                request.method, request.url.path, respuesta.status_code, milisegundos,
            )
            respuesta.headers["X-Request-ID"] = request_id
            return respuesta
        finally:
            request_id_var.reset(token)

    @app.exception_handler(OperationalError)
    async def base_no_disponible(request: Request, exc: OperationalError):
        # Conexion rechazada, timeout o consulta cancelada: reintentable.
        logger.error(
            "Base de datos no disponible o lenta (%s): %s",
            type(exc.orig).__name__, str(exc.orig).strip().splitlines()[0] if exc.orig else "",
        )
        return _respuesta_error(
            503,
            "El servicio de datos no esta disponible. Intente de nuevo en unos segundos.",
            request_id_var.get(),
            {"Retry-After": "5"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def error_de_base(request: Request, exc: SQLAlchemyError):
        logger.error("Error de base de datos (%s)", type(exc).__name__, exc_info=exc)
        return _respuesta_error(500, "Error interno del servidor.", request_id_var.get())

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request: Request, exc: RequestValidationError):
        # Igual que FastAPI, pero sin `input` ni `ctx`: no se devuelve lo enviado.
        errores = [
            {"loc": list(e.get("loc", ())), "msg": e.get("msg", ""), "type": e.get("type", "")}
            for e in exc.errors()
        ]
        respuesta = JSONResponse(
            status_code=422, content={"detail": errores, "request_id": request_id_var.get()}
        )
        respuesta.headers["X-Request-ID"] = request_id_var.get()
        return respuesta
