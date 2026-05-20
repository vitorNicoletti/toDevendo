from sqlalchemy.orm import Session
from src.controllers import usuario_controller as uc
from src.models.usuario import Usuario
from src.models.usuario_lid import UsuarioLid


def get_usuario_por_lid(session: Session, lid: str) -> Usuario | None:
    """Retorna o Usuario vinculado a um @lid, ou None se não houver vínculo."""
    vinculo = session.query(UsuarioLid).filter_by(lid=lid).first()
    if not vinculo:
        return None
    return uc.get_by_id(session, vinculo.id_usuario)


def existe_vinculo(session: Session, lid: str) -> bool:
    """True se o @lid já está vinculado a algum usuário (cache populado)."""
    return session.query(UsuarioLid).filter_by(lid=lid).first() is not None


def cachear_vinculos(session: Session, mapa: dict[str, str]) -> None:
    """Recebe {lid: telefone} e cria/atualiza o vínculo de cada lid cujo
    telefone já pertence a um Usuario cadastrado. Lids de pessoas não
    cadastradas são ignorados (não há a quem vincular)."""
    for lid, telefone in mapa.items():
        usuario = uc.get_by_telefone(session, telefone)
        if not usuario:
            continue
        vinculo = session.query(UsuarioLid).filter_by(lid=lid).first()
        if vinculo:
            if vinculo.id_usuario != usuario.id:
                vinculo.id_usuario = usuario.id
        else:
            session.add(UsuarioLid(lid=lid, id_usuario=usuario.id))
    session.commit()
