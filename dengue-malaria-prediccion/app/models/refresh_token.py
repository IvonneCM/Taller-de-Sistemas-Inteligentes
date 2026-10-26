"""Modelo ORM: refresh_tokens (TASK-017 / REQ-019, SEG-01).

Un JWT stateless no puede revocarse por si solo. Esta tabla guarda el `jti`
del refresh token emitido en el login para poder invalidarlo en logout o en
la rotacion de tokens.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expira_en = Column(DateTime(timezone=True), nullable=False)
    revocado_en = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    usuario = relationship("Usuario", back_populates="refresh_tokens")
