from sqlalchemy.orm import Session
from src.models.usuario import Usuario

NOME_MIN = 2
NOME_MAX = 255
PIX_MAX = 40


def _validar_nome(nome: str) -> str:
    nome = (nome or "").strip()
    if len(nome) < NOME_MIN:
        raise ValueError(f"Nome precisa ter pelo menos {NOME_MIN} caracteres.")
    if len(nome) > NOME_MAX:
        raise ValueError(f"Nome não pode ter mais de {NOME_MAX} caracteres.")
    return nome


def _validar_pix(chave: str) -> str:
    chave = (chave or "").strip()
    if not chave:
        raise ValueError("Chave Pix não pode ser vazia.")
    if len(chave) > PIX_MAX:
        raise ValueError(f"Chave Pix não pode ter mais de {PIX_MAX} caracteres.")
    return chave


def cadastrar(session: Session, telefone: str, nome: str) -> tuple[Usuario, bool]:
    """Retorna (usuario, criado). Se já existe, atualiza o nome."""
    nome = _validar_nome(nome)
    usuario = session.query(Usuario).filter_by(telefone=telefone).first()
    if usuario:
        usuario.nome = nome
        session.commit()
        return usuario, False
    usuario = Usuario(telefone=telefone, nome=nome)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario, True


def get_by_telefone(session: Session, telefone: str) -> Usuario | None:
    return session.query(Usuario).filter_by(telefone=telefone).first()


def get_by_id(session: Session, id_usuario: int) -> Usuario | None:
    return session.query(Usuario).filter_by(id=id_usuario).first()


def salvar_pix(session: Session, telefone: str, chave: str) -> Usuario:
    chave = _validar_pix(chave)
    usuario = session.query(Usuario).filter_by(telefone=telefone).first()
    if not usuario:
        raise ValueError("Você ainda não está cadastrado. Use !cadastro Seu Nome primeiro.")
    usuario.chave_pix = chave
    session.commit()
    return usuario
