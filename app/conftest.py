"""Configuração compartilhada dos testes.

Coloca o diretório `app/` no sys.path (para os imports `from src...`
funcionarem) e oferece a fixture `db`: uma sessão SQLAlchemy ligada a um
banco SQLite em memória, recriado do zero a cada teste.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base

# importa todos os models para registrá-los em Base.metadata
from src.models.usuario import Usuario  # noqa: F401,E402
from src.models.divida import Divida  # noqa: F401,E402


@pytest.fixture
def db():
    """Sessão isolada num SQLite em memória, com chaves estrangeiras ativas."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _ativar_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
