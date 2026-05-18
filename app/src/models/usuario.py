from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Usuario(Base):
    __tablename__ = "Usuario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    dt_registro: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    chave_pix: Mapped[str | None] = mapped_column(String(40), nullable=True)
