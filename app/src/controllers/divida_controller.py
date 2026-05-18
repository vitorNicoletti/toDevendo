from datetime import datetime
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from src.models.divida import Divida, StatusDivida

VALOR_MAX = Decimal("9999999.99")
DESC_MAX = 512


def _validar_valor(raw: str) -> Decimal:
    try:
        valor = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"Valor inválido: {raw!r}")
    if valor <= 0:
        raise ValueError("Valor precisa ser maior que zero.")
    if valor > VALOR_MAX:
        raise ValueError(f"Valor não pode passar de {VALOR_MAX}.")
    return valor.quantize(Decimal("0.01"))


def _validar_descricao(descricao: str) -> str:
    descricao = (descricao or "").strip()
    if not descricao:
        raise ValueError("Descrição não pode ser vazia.")
    if len(descricao) > DESC_MAX:
        raise ValueError(f"Descrição não pode ter mais de {DESC_MAX} caracteres.")
    return descricao


def registrar(
    session: Session,
    id_devedor: int,
    id_credor: int,
    id_registrou: int,
    valor_raw: str,
    descricao: str,
    dt_ocorrencia: datetime | None = None,
) -> Divida:
    if id_devedor == id_credor:
        raise ValueError("Devedor e credor não podem ser a mesma pessoa.")
    valor = _validar_valor(valor_raw)
    descricao = _validar_descricao(descricao)
    divida = Divida(
        id_devedor=id_devedor,
        id_credor=id_credor,
        id_registrou_a_divida=id_registrou,
        valor=valor,
        descricao=descricao,
        dt_ocorrencia=dt_ocorrencia or datetime.now(),
    )
    session.add(divida)
    session.commit()
    session.refresh(divida)
    return divida


def listar_devedores(session: Session, id_credor: int) -> list[Divida]:
    """Dívidas pendentes em que eu sou credor (o que me devem)."""
    return (
        session.query(Divida)
        .filter(Divida.status == StatusDivida.pendente, Divida.id_credor == id_credor)
        .order_by(Divida.dt_ocorrencia)
        .all()
    )


def listar_credores(session: Session, id_devedor: int) -> list[Divida]:
    """Dívidas pendentes em que eu sou devedor (o que eu devo)."""
    return (
        session.query(Divida)
        .filter(Divida.status == StatusDivida.pendente, Divida.id_devedor == id_devedor)
        .order_by(Divida.dt_ocorrencia)
        .all()
    )


def quitar(session: Session, id_divida: int, sender_id: int) -> Divida:
    divida = session.query(Divida).filter_by(id_divida=id_divida).first()
    if not divida:
        raise ValueError(f"Dívida #{id_divida} não encontrada.")
    if divida.status != StatusDivida.pendente:
        raise ValueError(f"Dívida #{id_divida} já está {divida.status.value}.")
    if sender_id not in (divida.id_credor, divida.id_devedor):
        raise ValueError("Só o credor ou o devedor podem marcar como paga.")
    divida.status = StatusDivida.pago
    divida.pago_em = datetime.now()
    session.commit()
    return divida


def cancelar(session: Session, id_divida: int, sender_id: int) -> Divida:
    divida = session.query(Divida).filter_by(id_divida=id_divida).first()
    if not divida:
        raise ValueError(f"Dívida #{id_divida} não encontrada.")
    if divida.status != StatusDivida.pendente:
        raise ValueError(f"Dívida #{id_divida} já está {divida.status.value}.")
    if sender_id != divida.id_registrou_a_divida:
        raise ValueError("Só quem registrou a dívida pode cancelar.")
    divida.status = StatusDivida.cancelado
    session.commit()
    return divida
