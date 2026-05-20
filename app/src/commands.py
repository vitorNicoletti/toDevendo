from sqlalchemy.orm import Session
from src.controllers import usuario_controller as uc
from src.controllers import divida_controller as dc
from src.views import mensagem_view as view


def dispatch(text: str, remetente_tel: str, mencionados: list[str], db: Session) -> str | None:
    """
    Recebe a mensagem e retorna o texto de resposta, ou None se não for um comando.
    remetente_tel: telefone canônico (só dígitos) de quem enviou.
    mencionados: lista de telefones canônicos mencionados na mensagem.
    """
    parts = text.strip().split()
    if not parts or not parts[0].startswith("!"):
        return None

    cmd = parts[0].lower()
    args = parts[1:]

    try:
        if cmd == "!cadastro":
            return _cadastro(remetente_tel, args, db)
        if cmd == "!pix":
            return _pix(remetente_tel, args, mencionados, db)
        if cmd == "!deve":
            return _deve(remetente_tel, args, mencionados, db)
        if cmd == "!devo":
            return _devo(remetente_tel, args, mencionados, db)
        if cmd == "!pago":
            return _pago(remetente_tel, args, db)
        if cmd == "!cancelar":
            return _cancelar(remetente_tel, args, db)
        if cmd == "!ajuda":
            return view.ajuda()
    except ValueError as e:
        return f"❌ {e}"

    return None


def _cadastro(remetente_tel: str, args: list[str], db: Session) -> str:
    if not args:
        return view.comando_invalido("!cadastro — use: !cadastro Seu Nome")
    # telefone canônico é só dígitos; se não for, a resolução do @lid falhou
    if not remetente_tel.isdigit():
        return view.nao_identificado()
    nome = " ".join(args)
    usuario, criado = uc.cadastrar(db, remetente_tel, nome)
    return view.cadastro_criado(usuario) if criado else view.cadastro_atualizado(usuario)


def _pix(remetente_tel: str, args: list[str], mencionados: list[str], db: Session) -> str:
    if args and args[0] == "-save":
        if len(args) < 2:
            return view.comando_invalido("!pix -save — use: !pix -save <chave>")
        chave = args[1]
        usuario = uc.salvar_pix(db, remetente_tel, chave)
        return view.pix_salvo(usuario)

    if mencionados:
        alvo_tel = mencionados[0]
        alvo = uc.get_by_telefone(db, alvo_tel)
        if not alvo:
            return view.usuario_nao_encontrado()
        return view.pix_outro(alvo)

    remetente = uc.get_by_telefone(db, remetente_tel)
    if not remetente:
        return view.usuario_nao_cadastrado()
    return view.pix_proprio(remetente)


def _descricao_de(args: list[str]) -> str:
    """Junta os args ignorando tokens que comecem com @ (menções)."""
    return " ".join(a for a in args if not a.startswith("@"))


def _deve(remetente_tel: str, args: list[str], mencionados: list[str], db: Session) -> str:
    if not args:
        sender = uc.get_by_telefone(db, remetente_tel)
        if not sender:
            return view.usuario_nao_cadastrado()
        dividas = dc.listar_devedores(db, sender.id)
        nomes = {d.id_devedor: _nome(db, d.id_devedor) for d in dividas}
        return view.lista_devedores(dividas, nomes)

    return _registrar_divida(remetente_tel, args, mencionados, db, sender_eh_credor=True)


def _devo(remetente_tel: str, args: list[str], mencionados: list[str], db: Session) -> str:
    if not args:
        sender = uc.get_by_telefone(db, remetente_tel)
        if not sender:
            return view.usuario_nao_cadastrado()
        dividas = dc.listar_credores(db, sender.id)
        nomes = {d.id_credor: _nome(db, d.id_credor) for d in dividas}
        return view.lista_credores(dividas, nomes)

    return _registrar_divida(remetente_tel, args, mencionados, db, sender_eh_credor=False)


def _registrar_divida(
    remetente_tel: str,
    args: list[str],
    mencionados: list[str],
    db: Session,
    sender_eh_credor: bool,
) -> str:
    cmd_nome = "!deve" if sender_eh_credor else "!devo"
    if len(args) < 3 or not mencionados:
        return view.comando_invalido(f"{cmd_nome} — use: {cmd_nome} <valor> @pessoa [@outra ...] <descrição>")

    valor_raw = args[0]
    descricao = _descricao_de(args[1:])

    sender = uc.get_by_telefone(db, remetente_tel)
    if not sender:
        return view.usuario_nao_cadastrado()

    criadas: list = []
    nao_cadastrados: list[str] = []
    vistos: set[int] = set()

    for tel in mencionados:
        outro = uc.get_by_telefone(db, tel)
        if not outro:
            nao_cadastrados.append(tel)
            continue
        if outro.id == sender.id or outro.id in vistos:
            continue
        vistos.add(outro.id)

        if sender_eh_credor:
            id_devedor, id_credor = outro.id, sender.id
            nome_devedor, nome_credor = outro.nome, sender.nome
        else:
            id_devedor, id_credor = sender.id, outro.id
            nome_devedor, nome_credor = sender.nome, outro.nome

        divida = dc.registrar(
            db,
            id_devedor=id_devedor,
            id_credor=id_credor,
            id_registrou=sender.id,
            valor_raw=valor_raw,
            descricao=descricao,
        )
        criadas.append((divida, nome_devedor, nome_credor))

    if not criadas:
        return view.usuario_nao_encontrado()

    return view.dividas_registradas(criadas, nao_cadastrados)


def _pago(remetente_tel: str, args: list[str], db: Session) -> str:
    if not args:
        return view.comando_invalido("!pago — use: !pago <id>")
    try:
        id_divida = int(args[0])
    except ValueError:
        raise ValueError(f"ID inválido: {args[0]!r}")

    sender = uc.get_by_telefone(db, remetente_tel)
    if not sender:
        return view.usuario_nao_cadastrado()

    divida = dc.quitar(db, id_divida, sender.id)
    return view.divida_quitada(divida)


def _cancelar(remetente_tel: str, args: list[str], db: Session) -> str:
    if not args:
        return view.comando_invalido("!cancelar — use: !cancelar <id>")
    try:
        id_divida = int(args[0])
    except ValueError:
        raise ValueError(f"ID inválido: {args[0]!r}")

    sender = uc.get_by_telefone(db, remetente_tel)
    if not sender:
        return view.usuario_nao_cadastrado()

    divida = dc.cancelar(db, id_divida, sender.id)
    return view.divida_cancelada(divida)


def _nome(db: Session, id_usuario: int) -> str:
    u = uc.get_by_id(db, id_usuario)
    return u.nome if u else "?"
