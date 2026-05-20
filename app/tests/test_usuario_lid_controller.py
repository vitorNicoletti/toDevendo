from src.controllers import usuario_controller as uc
from src.controllers import usuario_lid_controller as ulc


def test_get_usuario_por_lid_sem_vinculo(db):
    assert ulc.get_usuario_por_lid(db, "123@lid") is None


def test_existe_vinculo_falso_quando_nao_ha(db):
    assert ulc.existe_vinculo(db, "123@lid") is False


def test_cachear_vinculos_liga_usuario_cadastrado(db):
    usuario, _ = uc.cadastrar(db, "5511999999999", "João")
    ulc.cachear_vinculos(db, {"123@lid": "5511999999999"})

    assert ulc.existe_vinculo(db, "123@lid") is True
    assert ulc.get_usuario_por_lid(db, "123@lid").id == usuario.id


def test_cachear_vinculos_ignora_nao_cadastrado(db):
    # ninguém com esse telefone existe
    ulc.cachear_vinculos(db, {"999@lid": "5500000000000"})
    assert ulc.existe_vinculo(db, "999@lid") is False


def test_cachear_vinculos_atualiza_vinculo_existente(db):
    antigo, _ = uc.cadastrar(db, "5511111111111", "Ana")
    novo, _ = uc.cadastrar(db, "5522222222222", "Bruno")

    ulc.cachear_vinculos(db, {"abc@lid": "5511111111111"})
    assert ulc.get_usuario_por_lid(db, "abc@lid").id == antigo.id

    # o mesmo lid passa a apontar para outro telefone/usuário
    ulc.cachear_vinculos(db, {"abc@lid": "5522222222222"})
    assert ulc.get_usuario_por_lid(db, "abc@lid").id == novo.id


def test_cachear_vinculos_um_usuario_varios_lids(db):
    usuario, _ = uc.cadastrar(db, "5511999999999", "João")
    ulc.cachear_vinculos(db, {
        "lid-1@lid": "5511999999999",
        "lid-2@lid": "5511999999999",
    })
    assert ulc.get_usuario_por_lid(db, "lid-1@lid").id == usuario.id
    assert ulc.get_usuario_por_lid(db, "lid-2@lid").id == usuario.id
