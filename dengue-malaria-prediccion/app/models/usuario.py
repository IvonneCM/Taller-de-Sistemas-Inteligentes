"""Modelo ORM: usuarios. Implementa TASK-007 / REQ-019, REQ-020.

No incluye NINGUN campo de dato personal de paciente (nombre completo de
paciente, CI, historia clinica, etc.) — ver CLAUDE.md regla 2 y REQ-020.
Este `usuarios` es exclusivamente para el personal que opera el sistema
(autoridades, SEDES, epidemiologos, coordinadores, admin), no para
pacientes. `password_hash` se calcula con bcrypt en app/core/security.py
(TASK-003/017, fuera de alcance de esta tarea) — este modelo solo almacena
el hash, nunca una contrasena en texto plano.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, validates

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    municipio_asignado_id = Column(
        Integer, ForeignKey("municipios.id"), nullable=True
    )

    rol = relationship("Rol", back_populates="usuarios")
    municipio_asignado = relationship("Municipio")
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("password_hash")
    def _validar_no_texto_plano(self, key, value):
        """Verificacion defensiva: un hash de bcrypt siempre empieza con
        '$2'. Si alguien intenta asignar una contrasena en texto plano
        directamente al modelo (en vez de pasar por security.hash_password),
        se rechaza aqui mismo — soporta la verificacion de TASK-007."""
        if not isinstance(value, str) or not value.startswith("$2"):
            raise ValueError(
                "password_hash debe ser un hash bcrypt (prefijo '$2'), "
                "nunca una contrasena en texto plano."
            )
        return value
