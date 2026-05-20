from decimal import Decimal

import pytest

from src.controllers import divida_controller as dc
from src.controllers import usuario_controller as uc
from src.models.divida import StatusDivida


@pytest.fixture
def usuarios(db):
    """Cria três usuários e devolve seus ids."""
    a, _ = uc.cadastrar(db, "5511111111111", "Ana")
    b, _ = uc.cadastrar(db, "5522222222222", "Bruno")
    c, _ = uc.cadastrar(db, "5533333333333", "Carla")
    return a.id, b.id, c.id


# --- _validar_valor (via registrar) ---

def test_valor_invalido(db, usuarios):
    a, b, _ = usuarios
    with pytest.raises(ValueError):
        dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=a,
                     valor_raw="abc", descricao="x")


def test_valor_zero_ou_negativo(db, usuarios):
    a, b, _ = usuarios
    with pytest.raises(ValueError):
        dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=a,
                     valor_raw="0", descricao="x")


def test_valor_acima_do_maximo(db, usuarios):
    a, b, _ = usuarios
    with pytest.raises(ValueError):
        dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=a,
                     valor_raw="99999999", descricao="x")


def test_valor_aceita_virgula_decimal(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=a,
                          valor_raw="12,50", descricao="café")
    assert divida.valor == Decimal("12.50")


# --- _validar_descricao ---

def test_descricao_vazia(db, usuarios):
    a, b, _ = usuarios
    with pytest.raises(ValueError):
        dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=a,
                     valor_raw="10", descricao="   ")


# --- registrar ---

def test_registrar_devedor_igual_credor(db, usuarios):
    a, _, _ = usuarios
    with pytest.raises(ValueError):
        dc.registrar(db, id_devedor=a, id_credor=a, id_registrou=a,
                     valor_raw="10", descricao="x")


def test_registrar_cria_divida_pendente(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="30", descricao="uber")
    assert divida.id_divida is not None
    assert divida.status == StatusDivida.pendente


# --- listar ---

def test_listar_devedores_e_credores(db, usuarios):
    a, b, c = usuarios
    dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                 valor_raw="10", descricao="x")
    dc.registrar(db, id_devedor=c, id_credor=b, id_registrou=b,
                 valor_raw="20", descricao="y")

    devem_para_b = dc.listar_devedores(db, b)
    assert len(devem_para_b) == 2

    a_deve = dc.listar_credores(db, a)
    assert len(a_deve) == 1


def test_listar_ignora_dividas_quitadas(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    dc.quitar(db, divida.id_divida, sender_id=b)
    assert dc.listar_devedores(db, b) == []


# --- quitar ---

def test_quitar_divida_inexistente(db):
    with pytest.raises(ValueError):
        dc.quitar(db, 999, sender_id=1)


def test_quitar_marca_como_pago(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    quitada = dc.quitar(db, divida.id_divida, sender_id=a)
    assert quitada.status == StatusDivida.pago
    assert quitada.pago_em is not None


def test_quitar_duas_vezes_falha(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    dc.quitar(db, divida.id_divida, sender_id=a)
    with pytest.raises(ValueError):
        dc.quitar(db, divida.id_divida, sender_id=a)


def test_quitar_por_terceiro_falha(db, usuarios):
    a, b, c = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    with pytest.raises(ValueError):
        dc.quitar(db, divida.id_divida, sender_id=c)


# --- cancelar ---

def test_cancelar_so_quem_registrou(db, usuarios):
    a, b, _ = usuarios
    # registrada por b; a não pode cancelar
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    with pytest.raises(ValueError):
        dc.cancelar(db, divida.id_divida, sender_id=a)


def test_cancelar_marca_como_cancelado(db, usuarios):
    a, b, _ = usuarios
    divida = dc.registrar(db, id_devedor=a, id_credor=b, id_registrou=b,
                          valor_raw="10", descricao="x")
    cancelada = dc.cancelar(db, divida.id_divida, sender_id=b)
    assert cancelada.status == StatusDivida.cancelado


def test_cancelar_divida_inexistente(db):
    with pytest.raises(ValueError):
        dc.cancelar(db, 999, sender_id=1)
