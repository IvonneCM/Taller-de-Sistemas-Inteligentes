"""Limite de intentos fallidos de login (TASK-035, hallazgo H-3, NFR-005).

Cuenta los intentos FALLIDOS dentro de una ventana deslizante, por correo y por
direccion IP. Superado el maximo, el login responde 429 con `Retry-After` sin
siquiera comparar la contrasena. Un login correcto borra el contador del correo.

Limites conocidos (documentados en docs/revision_seguridad.md):
- El estado vive en la memoria del proceso: vale para una instancia (Render
  gratuito). Con varias instancias o reinicios, cada una cuenta aparte.
- Bloquear por correo permite que alguien impida a un usuario entrar durante la
  ventana enviando contrasenas falsas. Se acepta porque la ventana es corta y el
  caso contrario (probar claves sin freno) es peor para un sistema de salud.
- La IP sale de `request.client`; detras del proxy de Render uvicorn la toma de
  `X-Forwarded-For` (`--proxy-headers`).
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque

_MAX_CLAVES = 10_000  # tope de memoria: ante un ataque con muchos correos distintos


class LimiteIntentos:
    def __init__(self, ventana_segundos: int = 900, reloj=time.monotonic):
        self._ventana = ventana_segundos
        self._reloj = reloj
        self._fallos: dict[str, deque[float]] = {}
        self._cerrojo = threading.Lock()

    def configurar(self, ventana_segundos: int) -> None:
        self._ventana = ventana_segundos

    def _vigentes(self, clave: str, ahora: float) -> deque[float]:
        fallos = self._fallos.get(clave)
        if fallos is None:
            return deque()
        while fallos and ahora - fallos[0] >= self._ventana:
            fallos.popleft()
        if not fallos:
            del self._fallos[clave]
        return fallos

    def segundos_de_espera(self, clave: str, maximo: int) -> int:
        """0 si aun puede intentar; si no, segundos hasta que se libere un cupo."""
        with self._cerrojo:
            ahora = self._reloj()
            fallos = self._vigentes(clave, ahora)
            if len(fallos) < maximo:
                return 0
            return max(1, math.ceil(self._ventana - (ahora - fallos[0])))

    def registrar_fallo(self, clave: str) -> None:
        with self._cerrojo:
            ahora = self._reloj()
            if len(self._fallos) >= _MAX_CLAVES and clave not in self._fallos:
                for existente in list(self._fallos):
                    self._vigentes(existente, ahora)
                if len(self._fallos) >= _MAX_CLAVES:
                    return  # sin espacio: no se agranda la memoria
            self._fallos.setdefault(clave, deque()).append(ahora)

    def olvidar(self, clave: str) -> None:
        with self._cerrojo:
            self._fallos.pop(clave, None)

    def reiniciar(self) -> None:
        with self._cerrojo:
            self._fallos.clear()


# Instancia unica del proceso; la ventana se fija al primer uso desde la configuracion.
limite_login = LimiteIntentos()
