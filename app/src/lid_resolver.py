import httpx
from sqlalchemy.orm import Session
from src.models.lid_map import LidMap


def _is_lid(jid: str) -> bool:
    return isinstance(jid, str) and jid.endswith("@lid")


def _extract_ids(participant: dict) -> tuple[str | None, str | None]:
    """Extrai (lid, pn) de um participante WAHA, tolerando variações de schema entre engines."""
    pid = participant.get("id")
    serialized = pid.get("_serialized") if isinstance(pid, dict) else pid

    lid = None
    pn = participant.get("phoneNumber") or participant.get("pn")

    if isinstance(serialized, str):
        if serialized.endswith("@lid"):
            lid = serialized
        elif serialized.endswith("@c.us") or serialized.endswith("@s.whatsapp.net"):
            pn = pn or serialized

    # alguns engines retornam dois campos lado a lado
    alt_lid = participant.get("lid")
    if isinstance(alt_lid, str) and alt_lid.endswith("@lid"):
        lid = lid or alt_lid

    if isinstance(pn, str) and not (pn.endswith("@c.us") or pn.endswith("@s.whatsapp.net")):
        # pn pode vir como número puro "5511999..."; normaliza
        pn = f"{pn.lstrip('+').split('@')[0]}@c.us"

    return lid, pn


async def populate_from_group(
    group_id: str,
    db: Session,
    http: httpx.AsyncClient,
    waha_url: str,
    waha_api_key: str | None,
    waha_session: str,
) -> int:
    """Busca participantes do grupo na WAHA e popula o LidMap. Retorna quantos foram salvos/atualizados."""
    headers = {"X-Api-Key": waha_api_key} if waha_api_key else {}
    r = await http.get(
        f"{waha_url}/api/{waha_session}/groups/{group_id}/participants",
        headers=headers,
    )
    if r.status_code != 200:
        return 0

    salvos = 0
    for p in r.json() or []:
        lid, pn = _extract_ids(p)
        if not lid or not pn or lid == pn:
            continue
        existente = db.query(LidMap).filter_by(lid=lid).first()
        if existente:
            if existente.pn != pn:
                existente.pn = pn
                salvos += 1
        else:
            db.add(LidMap(lid=lid, pn=pn))
            salvos += 1
    db.commit()
    return salvos


async def resolve(
    jid: str,
    group_id: str | None,
    db: Session,
    http: httpx.AsyncClient,
    waha_url: str,
    waha_api_key: str | None,
    waha_session: str,
) -> str:
    """Resolve @lid → @c.us via cache + WAHA. Se não conseguir resolver, retorna o jid original."""
    if not _is_lid(jid):
        return jid

    cached = db.query(LidMap).filter_by(lid=jid).first()
    if cached:
        return cached.pn

    if not group_id or not group_id.endswith("@g.us"):
        return jid

    await populate_from_group(group_id, db, http, waha_url, waha_api_key, waha_session)

    cached = db.query(LidMap).filter_by(lid=jid).first()
    return cached.pn if cached else jid


async def resolve_many(
    jids: list[str],
    group_id: str | None,
    db: Session,
    http: httpx.AsyncClient,
    waha_url: str,
    waha_api_key: str | None,
    waha_session: str,
) -> list[str]:
    """Resolve uma lista, evitando múltiplas chamadas à WAHA quando vários LIDs vêm do mesmo grupo."""
    if not jids:
        return []

    lids = [j for j in jids if _is_lid(j)]
    if lids and group_id and group_id.endswith("@g.us"):
        faltam = [
            l for l in lids
            if not db.query(LidMap).filter_by(lid=l).first()
        ]
        if faltam:
            await populate_from_group(group_id, db, http, waha_url, waha_api_key, waha_session)

    resolvidos = []
    for j in jids:
        if not _is_lid(j):
            resolvidos.append(j)
            continue
        cached = db.query(LidMap).filter_by(lid=j).first()
        resolvidos.append(cached.pn if cached else j)
    return resolvidos
