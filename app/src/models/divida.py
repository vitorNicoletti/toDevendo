from sqlalchemy import ForeignKey, Numeric, String, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import enum


class StatusDivida(str, enum.Enum):
    pendente = "pendente"
    pago = "pago"
    cancelado = "cancelado"


class Divida(Base):
    __tablename__ = "Divida"

    id_divida: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_devedor: Mapped[int] = mapped_column(ForeignKey("Usuario.id"), nullable=False)
    id_credor: Mapped[int] = mapped_column(ForeignKey("Usuario.id"), nullable=False)
    id_registrou_a_divida: Mapped[int] = mapped_column(ForeignKey("Usuario.id"), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(String(512), nullable=True)
    dt_ocorrencia: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    dt_registro: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[StatusDivida] = mapped_column(
        Enum(StatusDivida), nullable=False, default=StatusDivida.pendente
    )
    pago_em: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
