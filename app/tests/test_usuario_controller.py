import pytest

from src.controllers import usuario_controller as uc


# --- _validar_nome (via cadastrar) ---

def test_cadastro_rejeita_nome_curto(db):
    with pytest.raises(ValueError):
        uc.cadastrar(db, "5511999999999", "a")


def test_cadastro_rejeita_nome_longo(db):
    with pytest.raises(ValueError):
        uc.cadastrar(db, "5511999999999", "x" * 256)


def test_cadastro_remove_espacos_do_nome(db):
    usuario, _ = uc.cadastrar(db, "5511999999999", "  João  ")
    assert usuario.nome == "João"


# --- cadastrar ---

def test_cadastrar_cria_usuario_novo(db):
    usuario, criado = uc.cadastrar(db, "5511999999999", "João")
    assert criado is True
    assert usuario.id is not None
    assert usuario.telefone == "5511999999999"


def test_cadastrar_existente_atualiza_nome(db):
    uc.cadastrar(db, "5511999999999", "João")
    usuario, criado = uc.cadastrar(db, "5511999999999", "João Silva")
    assert criado is False
    assert usuario.nome == "João Silva"


# --- get_by_telefone / get_by_id ---

def test_get_by_telefone_encontra(db):
    criado, _ = uc.cadastrar(db, "5511999999999", "João")
    assert uc.get_by_telefone(db, "5511999999999").id == criado.id


def test_get_by_telefone_inexistente_retorna_none(db):
    assert uc.get_by_telefone(db, "0000") is None


def test_get_by_id(db):
    criado, _ = uc.cadastrar(db, "5511999999999", "João")
    assert uc.get_by_id(db, criado.id).telefone == "5511999999999"
    assert uc.get_by_id(db, 999999) is None


# --- salvar_pix ---

def test_salvar_pix_atualiza_usuario(db):
    uc.cadastrar(db, "5511999999999", "João")
    usuario = uc.salvar_pix(db, "5511999999999", "joao@pix.com")
    assert usuario.chave_pix == "joao@pix.com"


def test_salvar_pix_sem_cadastro_falha(db):
    with pytest.raises(ValueError):
        uc.salvar_pix(db, "5511999999999", "joao@pix.com")


def test_salvar_pix_vazia_falha(db):
    uc.cadastrar(db, "5511999999999", "João")
    with pytest.raises(ValueError):
        uc.salvar_pix(db, "5511999999999", "   ")


def test_salvar_pix_longa_falha(db):
    uc.cadastrar(db, "5511999999999", "João")
    with pytest.raises(ValueError):
        uc.salvar_pix(db, "5511999999999", "x" * 41)
