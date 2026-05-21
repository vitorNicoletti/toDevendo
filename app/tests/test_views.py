from decimal import Decimal

from src.models.usuario import Usuario
from src.models.divida import Divida
from src.views import mensagem_view as view


def _usuario(nome="João", chave_pix=None):
    return Usuario(nome=nome, chave_pix=chave_pix, jid="5511999999999@c.us")


def _divida(id_divida=1, valor="50.00", descricao="almoço", id_devedor=1, id_credor=2):
    return Divida(
        id_divida=id_divida,
        valor=Decimal(valor),
        descricao=descricao,
        id_devedor=id_devedor,
        id_credor=id_credor,
    )


# --- Usuario ---

def test_cadastro_criado_inclui_nome():
    assert "João" in view.cadastro_criado(_usuario("João"))


def test_cadastro_atualizado_inclui_nome():
    assert "Maria" in view.cadastro_atualizado(_usuario("Maria"))


def test_pix_proprio_sem_chave():
    assert "não tem chave Pix" in view.pix_proprio(_usuario(chave_pix=None)).lower() \
        or "não tem chave" in view.pix_proprio(_usuario(chave_pix=None))


def test_pix_proprio_com_chave():
    msg = view.pix_proprio(_usuario(chave_pix="meu@pix.com"))
    assert "meu@pix.com" in msg


def test_pix_outro_sem_chave_cita_nome():
    msg = view.pix_outro(_usuario("Ana", chave_pix=None))
    assert "Ana" in msg


def test_pix_outro_com_chave():
    msg = view.pix_outro(_usuario("Ana", chave_pix="123"))
    assert "Ana" in msg and "123" in msg


def test_pix_salvo_mostra_chave():
    assert "abc" in view.pix_salvo(_usuario(chave_pix="abc"))


def test_mensagens_de_erro_de_usuario():
    assert view.usuario_nao_cadastrado()
    assert view.usuario_nao_encontrado()


# --- Divida ---

def test_divida_registrada_tem_valor_e_nomes():
    msg = view.divida_registrada(_divida(valor="42.50"), "Pedro", "Lucas")
    assert "Pedro" in msg and "Lucas" in msg and "42.50" in msg


def test_dividas_registradas_uma_so():
    criadas = [(_divida(), "Pedro", "Lucas")]
    msg = view.dividas_registradas(criadas, nao_cadastrados=[])
    assert "Pedro" in msg and "Lucas" in msg


def test_dividas_registradas_varias():
    criadas = [
        (_divida(id_divida=1), "Pedro", "Lucas"),
        (_divida(id_divida=2), "Ana", "Lucas"),
    ]
    msg = view.dividas_registradas(criadas, nao_cadastrados=[])
    assert "2 dívidas" in msg


def test_dividas_registradas_avisa_nao_cadastrados():
    criadas = [(_divida(), "Pedro", "Lucas")]
    msg = view.dividas_registradas(criadas, nao_cadastrados=["999@lid"])
    assert "não cadastrado" in msg


def test_divida_quitada_e_cancelada():
    assert "#7" in view.divida_quitada(_divida(id_divida=7))
    assert "#9" in view.divida_cancelada(_divida(id_divida=9))


# --- Listas ---

def test_lista_devedores_vazia():
    assert view.lista_devedores([], {})


def test_lista_devedores_com_total():
    dividas = [_divida(id_divida=1, valor="10.00"), _divida(id_divida=2, valor="5.00")]
    nomes = {1: "Pedro"}
    msg = view.lista_devedores(dividas, nomes)
    assert "15.00" in msg


def test_lista_credores_vazia():
    assert view.lista_credores([], {})


def test_lista_credores_com_total():
    dividas = [_divida(id_divida=1, valor="20.00", id_credor=3)]
    msg = view.lista_credores(dividas, {3: "Lucas"})
    assert "20.00" in msg


# --- Geral ---

def test_comando_invalido_cita_o_comando():
    assert "!xpto" in view.comando_invalido("!xpto")


def test_ajuda_lista_comandos():
    msg = view.ajuda()
    for cmd in ("!cadastro", "!pix", "!deve", "!devo", "!pago", "!cancelar"):
        assert cmd in msg
