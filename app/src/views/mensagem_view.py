from src.models.usuario import Usuario
from src.models.divida import Divida


# --- Usuario ---

def cadastro_criado(usuario: Usuario) -> str:
    return f"✅ Cadastro criado! Bem-vindo, *{usuario.nome}*."


def cadastro_atualizado(usuario: Usuario) -> str:
    return f"✏️ Nome atualizado para *{usuario.nome}*."


def pix_proprio(usuario: Usuario) -> str:
    if not usuario.chave_pix:
        return "Você não tem chave Pix cadastrada. Use *!pix -save <chave>* para cadastrar."
    return f"Sua chave Pix: `{usuario.chave_pix}`"


def pix_outro(usuario: Usuario) -> str:
    if not usuario.chave_pix:
        return f"*{usuario.nome}* não tem chave Pix cadastrada."
    return f"Chave Pix de *{usuario.nome}*: `{usuario.chave_pix}`"


def pix_salvo(usuario: Usuario) -> str:
    return f"✅ Chave Pix `{usuario.chave_pix}` salva com sucesso!"


def usuario_nao_cadastrado() -> str:
    return "Você ainda não está cadastrado. Use *!cadastro Seu Nome* primeiro."


def usuario_nao_encontrado() -> str:
    return "❌ Usuário não encontrado. Ele precisa se cadastrar com *!cadastro Nome*."


def nao_identificado() -> str:
    return "❌ Não consegui te identificar agora. Tente novamente em alguns instantes."


# --- Divida ---

def divida_registrada(divida: Divida, nome_devedor: str, nome_credor: str) -> str:
    return (
        f"✅ Dívida registrada!\n"
        f"#{divida.id_divida} | *{nome_devedor}* deve R${divida.valor:.2f} para *{nome_credor}*\n"
        f"📝 {divida.descricao}"
    )


def dividas_registradas(
    criadas: list[tuple[Divida, str, str]],
    nao_cadastrados: list[str],
) -> str:
    if len(criadas) == 1:
        divida, nome_devedor, nome_credor = criadas[0]
        msg = divida_registrada(divida, nome_devedor, nome_credor)
    else:
        descricao = criadas[0][0].descricao
        valor = criadas[0][0].valor
        linhas = [f"✅ {len(criadas)} dívidas registradas (R${valor:.2f} cada — {descricao}):"]
        for divida, nome_devedor, nome_credor in criadas:
            linhas.append(f"#{divida.id_divida} | *{nome_devedor}* → *{nome_credor}*")
        msg = "\n".join(linhas)

    if nao_cadastrados:
        msg += f"\n⚠️ {len(nao_cadastrados)} mencionado(s) não cadastrado(s) — ignorado(s)."
    return msg


def divida_quitada(divida: Divida) -> str:
    return f"✅ Dívida #{divida.id_divida} marcada como paga!"


def divida_cancelada(divida: Divida) -> str:
    return f"🚫 Dívida #{divida.id_divida} cancelada."


def lista_devedores(dividas: list[Divida], nomes: dict[int, str]) -> str:
    if not dividas:
        return "🎉 Ninguém te deve nada!"
    total = sum(d.valor for d in dividas)
    linhas = ["📥 *Te devem:*"]
    for d in dividas:
        nome = nomes.get(d.id_devedor, "?")
        linhas.append(f"#{d.id_divida} | {nome} | R${d.valor:.2f} | {d.descricao or '-'}")
    linhas.append(f"💰 Total: R${total:.2f}")
    return "\n".join(linhas)


def lista_credores(dividas: list[Divida], nomes: dict[int, str]) -> str:
    if not dividas:
        return "🎉 Você não deve nada!"
    total = sum(d.valor for d in dividas)
    linhas = ["📤 *Você deve:*"]
    for d in dividas:
        nome = nomes.get(d.id_credor, "?")
        linhas.append(f"#{d.id_divida} | {nome} | R${d.valor:.2f} | {d.descricao or '-'}")
    linhas.append(f"💰 Total: R${total:.2f}")
    return "\n".join(linhas)


# --- Geral ---

def comando_invalido(cmd: str) -> str:
    return f"❓ Comando *{cmd}* inválido ou com argumentos errados."


def ajuda() -> str:
    return (
        "📖 *Comandos disponíveis:*\n"
        "!ajuda - mostra os comandos\n"
        "!cadastro <nome> — se cadastrar\n"
        "!pix — ver sua chave Pix\n"
        "!pix @pessoa — ver a chave Pix de alguém\n"
        "!pix -save <chave> — salvar sua chave Pix\n"
        "!deve <valor> @pessoa <descrição> — registrar que alguém te deve\n"
        "!devo <valor> @pessoa <descrição> — registrar que você deve a alguém\n"
        "!deve — listar o que te devem\n"
        "!devo — listar o que você deve\n"
        "!pago <id> — marcar dívida como paga\n"
        "!cancelar <id> — cancelar dívida que você registrou"
    )
