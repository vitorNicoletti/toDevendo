from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class LidMap(Base):
    __tablename__ = "LidMap"

    lid: Mapped[str] = mapped_column(String(64), primary_key=True)
    pn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
