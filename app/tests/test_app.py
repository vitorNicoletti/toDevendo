import pytest

from src import app as app_module
from src.app import _id_da_mensagem, _ja_processada


@pytest.fixture(autouse=True)
def _limpa_ids():
    """Zera a janela de IDs processados antes de cada teste."""
    app_module._ids_processados.clear()
    yield
    app_module._ids_processados.clear()


# --- _id_da_mensagem ---

def test_id_da_mensagem_string():
    assert _id_da_mensagem({"id": "abc123"}) == "abc123"


def test_id_da_mensagem_dict_serializado():
    assert _id_da_mensagem({"id": {"_serialized": "abc123"}}) == "abc123"


def test_id_da_mensagem_ausente():
    assert _id_da_mensagem({}) is None


def test_id_da_mensagem_vazio():
    assert _id_da_mensagem({"id": ""}) is None


# --- _ja_processada ---

def test_primeira_vez_nao_foi_processada():
    assert _ja_processada("msg-1") is False


def test_segunda_vez_foi_processada():
    _ja_processada("msg-1")
    assert _ja_processada("msg-1") is True


def test_ids_diferentes_sao_independentes():
    assert _ja_processada("msg-1") is False
    assert _ja_processada("msg-2") is False


def test_sem_id_nunca_e_duplicada():
    # sem ID não há como deduplicar — toda mensagem é tratada como nova
    assert _ja_processada(None) is False
    assert _ja_processada(None) is False


def test_janela_descarta_ids_antigos():
    limite = app_module._MAX_IDS_PROCESSADOS
    _ja_processada("antigo")
    # enche a janela com IDs novos, empurrando "antigo" para fora
    for i in range(limite):
        _ja_processada(f"novo-{i}")
    # "antigo" saiu da janela => seria reprocessado
    assert _ja_processada("antigo") is False
    # um ID recente continua marcado como processado
    assert _ja_processada(f"novo-{limite - 1}") is True
