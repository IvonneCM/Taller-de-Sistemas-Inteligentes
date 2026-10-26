"""Configuracion de la aplicacion leida desde variables de entorno.

TASK-003 (NFR-005, CLAUDE.md regla 6): ninguna credencial vive en el codigo.
Los valores salen del entorno o de un archivo `.env` (ver `.env.example`).
`DATABASE_URL` y `SECRET_KEY` no tienen valor por defecto a proposito: si
faltan, la aplicacion falla al arrancar en vez de usar un secreto inventado.
"""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de ejemplo de .env.example; nunca debe llegar a produccion.
_SECRET_KEY_EJEMPLO = "cambiar-por-una-clave-larga-y-aleatoria"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    # TASK-040 (NFR-003): diagnostico y limites de espera ante una base lenta o caida.
    LOG_LEVEL: str = "INFO"
    DB_CONNECT_TIMEOUT_SECONDS: int = 5
    DB_STATEMENT_TIMEOUT_MS: int = 15000
    # Limite de intentos fallidos de login (TASK-035, H-3); 0 desactiva el limite.
    LOGIN_MAX_INTENTOS_EMAIL: int = 5
    LOGIN_MAX_INTENTOS_IP: int = 20
    LOGIN_VENTANA_SEGUNDOS: int = 900
    DB_POOL_TIMEOUT_SECONDS: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalizar_esquema(cls, v: str) -> str:
        # Algunos proveedores entregan "postgres://", que SQLAlchemy 2 no acepta.
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://"):]
        return v

    @model_validator(mode="after")
    def _rechazar_secreto_debil_en_produccion(self) -> "Settings":
        if self.ENVIRONMENT == "production" and (
            self.SECRET_KEY == _SECRET_KEY_EJEMPLO or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "SECRET_KEY debe ser aleatoria y de al menos 32 caracteres "
                "cuando ENVIRONMENT=production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Settings se crea una sola vez; los tests pueden usar Settings(...) directo."""
    return Settings()
