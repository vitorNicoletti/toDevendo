import pytest

from src.controllers import usuario_controller as uc
from src.controllers import usuario_lid_controller as ulc
from src.lid_resolver import LidResolver

GRUPO = "120000@g.us"


# --- fake do cliente HTTP da WAHA ---

class _FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.text = str(data)

    def json(self):
        return self._data


class _FakeHttp:
    """Simula httpx.AsyncClient: registra as chamadas e devolve uma resposta fixa."""
    def __init__(self, status_code=200, data=None):
        self._response = _FakeResponse(status_code, data or [])
        self.chamadas = 0

    async def get(self, url, headers=None):
        self.chamadas += 1
        return self._response


def _resolver(db, http, group_id=GRUPO):
    return LidResolver(db, http, group_id, "http://waha", "key", "default")


# --- is_lid ---

@pytest.mark.parametrize("valor,esperado", [
    ("123@lid", True),
    ("5511999@c.us", False),
    ("5511999@s.whatsapp.net", False),
    ("", False),
    (None, False),
])
def test_is_lid(valor, esperado):
    assert LidResolver.is_lid(valor) is esperado


# --- so_digitos ---

@pytest.mark.parametrize("valor,esperado", [
    ("5511999999999@c.us", "5511999999999"),
    ("+55 11 99999-0000", "5511999990000"),
    ("5511888@s.whatsapp.net", "5511888"),
    ("", ""),
    (None, ""),
    ("abc", ""),
])
def test_so_digitos(valor, esperado):
    assert LidResolver.so_digitos(valor) == esperado


# --- _extrair_ids ---

def test_extrair_ids_com_lid_serializado_e_telefone():
    p = {"id": {"_serialized": "123@lid"}, "phoneNumber": "5511999999999"}
    assert LidResolver._extrair_ids(p) == ("123@lid", "5511999999999")


def test_extrair_ids_so_telefone():
    p = {"id": "5511888888888@c.us"}
    assert LidResolver._extrair_ids(p) == (None, "5511888888888")


def test_extrair_ids_campos_lado_a_lado():
    p = {"lid": "999@lid", "pn": "+55 11 5555-0000"}
    assert LidResolver._extrair_ids(p) == ("999@lid", "551155550000")


def test_extrair_ids_lid_sem_telefone():
    p = {"id": {"_serialized": "abc@lid"}}
    assert LidResolver._extrair_ids(p) == ("abc@lid", None)


# --- resolver ---

async def test_resolver_jid_de_telefone_nao_chama_waha(db):
    http = _FakeHttp()
    tel = await _resolver(db, http).resolver("5511999999999@c.us")
    assert tel == "5511999999999"
    assert http.chamadas == 0


async def test_resolver_lid_em_cache_nao_chama_waha(db):
    uc.cadastrar(db, "5511999999999", "João")
    ulc.cachear_vinculos(db, {"123@lid": "5511999999999"})

    http = _FakeHttp()
    tel = await _resolver(db, http).resolver("123@lid")
    assert tel == "5511999999999"
    assert http.chamadas == 0


async def test_resolver_lid_consulta_waha_e_cacheia(db):
    uc.cadastrar(db, "5511999999999", "João")
    http = _FakeHttp(data=[
        {"id": {"_serialized": "123@lid"}, "phoneNumber": "5511999999999"},
    ])

    tel = await _resolver(db, http).resolver("123@lid")
    assert tel == "5511999999999"
    assert http.chamadas == 1
    # o vínculo ficou em cache
    assert ulc.existe_vinculo(db, "123@lid")


async def test_resolver_lid_desconhecido_retorna_o_proprio_lid(db):
    http = _FakeHttp(data=[])  # WAHA não conhece ninguém
    tel = await _resolver(db, http).resolver("123@lid")
    assert tel == "123@lid"


async def test_resolver_lid_com_falha_da_waha(db):
    http = _FakeHttp(status_code=500)
    tel = await _resolver(db, http).resolver("123@lid")
    assert tel == "123@lid"


async def test_resolver_lid_sem_grupo_nao_chama_waha(db):
    http = _FakeHttp(data=[
        {"id": {"_serialized": "123@lid"}, "phoneNumber": "5511999999999"},
    ])
    tel = await _resolver(db, http, group_id=None).resolver("123@lid")
    assert tel == "123@lid"
    assert http.chamadas == 0


# --- resolver_muitos ---

async def test_resolver_muitos_lista_vazia(db):
    assert await _resolver(db, _FakeHttp()).resolver_muitos([]) == []


async def test_resolver_muitos_mistura_telefone_e_lid(db):
    uc.cadastrar(db, "5511999999999", "João")
    http = _FakeHttp(data=[
        {"id": {"_serialized": "123@lid"}, "phoneNumber": "5511999999999"},
    ])
    resultado = await _resolver(db, http).resolver_muitos(
        ["5500000000000@c.us", "123@lid", "desconhecido@lid"]
    )
    assert resultado == ["5500000000000", "5511999999999", "desconhecido@lid"]
    # uma única consulta à WAHA mesmo com dois lids
    assert http.chamadas == 1
