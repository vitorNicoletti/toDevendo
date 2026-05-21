import pytest

from src.controllers import usuario_controller as uc

JID = "223961136771243@lid"


# --- _validar_nome (via cadastrar) ---

def test_cadastro_rejeita_nome_curto(db):
    with pytest.raises(ValueError):
        uc.cadastrar(db, JID, "a")


def test_cadastro_rejeita_nome_longo(db):
    with pytest.raises(ValueError):
        uc.cadastrar(db, JID, "x" * 256)


def test_cadastro_remove_espacos_do_nome(db):
    usuario, _ = uc.cadastrar(db, JID, "  João  ")
    assert usuario.nome == "João"


# --- cadastrar ---

def test_cadastrar_cria_usuario_novo(db):
    usuario, criado = uc.cadastrar(db, JID, "João")
    assert criado is True
    assert usuario.id is not None
    assert usuario.jid == JID


def test_cadastrar_existente_atualiza_nome(db):
    uc.cadastrar(db, JID, "João")
    usuario, criado = uc.cadastrar(db, JID, "João Silva")
    assert criado is False
    assert usuario.nome == "João Silva"


# --- get_by_jid / get_by_id ---

def test_get_by_jid_encontra(db):
    criado, _ = uc.cadastrar(db, JID, "João")
    assert uc.get_by_jid(db, JID).id == criado.id


def test_get_by_jid_inexistente_retorna_none(db):
    assert uc.get_by_jid(db, "0000@lid") is None


def test_get_by_id(db):
    criado, _ = uc.cadastrar(db, JID, "João")
    assert uc.get_by_id(db, criado.id).jid == JID
    assert uc.get_by_id(db, 999999) is None


# --- salvar_pix ---

def test_salvar_pix_atualiza_usuario(db):
    uc.cadastrar(db, JID, "João")
    usuario = uc.salvar_pix(db, JID, "joao@pix.com")
    assert usuario.chave_pix == "joao@pix.com"


def test_salvar_pix_sem_cadastro_falha(db):
    with pytest.raises(ValueError):
        uc.salvar_pix(db, JID, "joao@pix.com")


def test_salvar_pix_vazia_falha(db):
    uc.cadastrar(db, JID, "João")
    with pytest.raises(ValueError):
        uc.salvar_pix(db, JID, "   ")


def test_salvar_pix_longa_falha(db):
    uc.cadastrar(db, JID, "João")
    with pytest.raises(ValueError):
        uc.salvar_pix(db, JID, "x" * 41)
