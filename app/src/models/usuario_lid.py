from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class UsuarioLid(Base):
    """Vínculo entre um ID opaco @lid do WhatsApp e um Usuario.
    Um usuário pode ter vários lids; cada lid pertence a um único usuário."""

    __tablename__ = "UsuarioLid"

    lid: Mapped[str] = mapped_column(String(64), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("Usuario.id"), nullable=False, index=True
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
