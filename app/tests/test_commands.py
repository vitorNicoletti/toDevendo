from src import commands
from src.controllers import usuario_controller as uc
from src.controllers import divida_controller as dc

ANA = "5511111111111"
BRUNO = "5522222222222"


def _disp(text, remetente=ANA, mencionados=None, db=None):
    return commands.dispatch(text, remetente, mencionados or [], db)


# --- dispatch / roteamento ---

def test_mensagem_comum_nao_e_comando(db):
    assert _disp("oi gente", db=db) is None


def test_comando_desconhecido_retorna_none(db):
    assert _disp("!naoexiste", db=db) is None


def test_ajuda(db):
    assert "Comandos" in _disp("!ajuda", db=db)


# --- !cadastro ---

def test_cadastro_sem_nome_invalido(db):
    assert "inválido" in _disp("!cadastro", db=db)


def test_cadastro_cria_usuario(db):
    resposta = _disp("!cadastro Ana Maria", remetente=ANA, db=db)
    assert "Ana Maria" in resposta
    assert uc.get_by_telefone(db, ANA).nome == "Ana Maria"


def test_cadastro_de_lid_nao_resolvido_e_recusado(db):
    # remetente não é só dígitos => resolução do @lid falhou
    resposta = _disp("!cadastro Ana", remetente="abc@lid", db=db)
    assert "identificar" in resposta
    assert uc.get_by_telefone(db, "abc@lid") is None


# --- !pix ---

def test_pix_proprio_sem_cadastro(db):
    assert "não está cadastrado" in _disp("!pix", db=db)


def test_pix_save_e_consulta(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    salvo = _disp("!pix -save ana@pix.com", remetente=ANA, db=db)
    assert "ana@pix.com" in salvo
    consulta = _disp("!pix", remetente=ANA, db=db)
    assert "ana@pix.com" in consulta


def test_pix_save_sem_argumento(db):
    assert "inválido" in _disp("!pix -save", db=db)


def test_pix_de_outro_por_mencao(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)
    _disp("!pix -save bruno@pix.com", remetente=BRUNO, db=db)

    resposta = _disp("!pix @bruno", remetente=ANA, mencionados=[BRUNO], db=db)
    assert "bruno@pix.com" in resposta


def test_pix_de_mencionado_inexistente(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    resposta = _disp("!pix @x", remetente=ANA, mencionados=["9999"], db=db)
    assert "não encontrado" in resposta


# --- !deve / !devo ---

def test_deve_registra_divida(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)

    resposta = _disp("!deve 50 @bruno almoço", remetente=ANA,
                     mencionados=[BRUNO], db=db)
    assert "registrada" in resposta
    # Ana é credora => Bruno deve a Ana
    ana = uc.get_by_telefone(db, ANA)
    assert len(dc.listar_devedores(db, ana.id)) == 1


def test_devo_registra_divida(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)

    _disp("!devo 30 @bruno uber", remetente=ANA, mencionados=[BRUNO], db=db)
    ana = uc.get_by_telefone(db, ANA)
    assert len(dc.listar_credores(db, ana.id)) == 1


def test_deve_sem_mencionar_e_sem_args_lista(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    assert "deve" in _disp("!deve", remetente=ANA, db=db).lower()


def test_deve_sem_cadastro_pede_cadastro(db):
    assert "cadastr" in _disp("!deve", remetente=ANA, db=db).lower()


def test_deve_valor_invalido_retorna_erro(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)
    resposta = _disp("!deve zero @bruno almoço", remetente=ANA,
                     mencionados=[BRUNO], db=db)
    assert resposta.startswith("❌")


def test_deve_mencionado_nao_cadastrado(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    resposta = _disp("!deve 10 @x cafe", remetente=ANA,
                     mencionados=["9999"], db=db)
    assert "não encontrado" in resposta


# --- !pago / !cancelar ---

def test_pago_marca_divida(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)
    _disp("!deve 50 @bruno almoço", remetente=ANA, mencionados=[BRUNO], db=db)

    ana = uc.get_by_telefone(db, ANA)
    id_divida = dc.listar_devedores(db, ana.id)[0].id_divida

    resposta = _disp(f"!pago {id_divida}", remetente=ANA, db=db)
    assert "paga" in resposta
    assert dc.listar_devedores(db, ana.id) == []


def test_pago_id_invalido(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    assert _disp("!pago abc", remetente=ANA, db=db).startswith("❌")


def test_cancelar_marca_divida(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    _disp("!cadastro Bruno", remetente=BRUNO, db=db)
    _disp("!deve 50 @bruno almoço", remetente=ANA, mencionados=[BRUNO], db=db)

    ana = uc.get_by_telefone(db, ANA)
    id_divida = dc.listar_devedores(db, ana.id)[0].id_divida

    resposta = _disp(f"!cancelar {id_divida}", remetente=ANA, db=db)
    assert "cancelada" in resposta


def test_cancelar_sem_id(db):
    _disp("!cadastro Ana", remetente=ANA, db=db)
    assert "inválido" in _disp("!cancelar", remetente=ANA, db=db)
