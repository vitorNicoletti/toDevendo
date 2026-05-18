from fastapi import FastAPI, Request, HTTPException
import httpx
import os

from src.database import get_session
from src import commands
from src import lid_resolver
from src.models.usuario import Usuario

app = FastAPI()

WAHA_URL = os.getenv("WAHA_URL", "http://waha:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_IDS", "naovaiacharnada")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    event = data.get("event")
    payload = data.get("payload", {})
    session = data.get("session", "default")

    from_me = payload.get("fromMe", False)
    text = payload.get("body", "")

    if not isinstance(text, str):
        return {"status": "ok"}

    to_id = payload.get("to", "")
    from_id = payload.get("from", "")
    is_group = to_id.endswith("@g.us") or from_id.endswith("@g.us")
    group_id = to_id if to_id.endswith("@g.us") else from_id

    sender_jid_raw = payload.get("participant") or from_id
    sender_name = payload.get("_data", {}).get("notifyName", "")

    from_bot = text.startswith("[NicoBot]")
    mentions_raw = payload.get("_data", {}).get("mentionedJidList", [])

    if event != "message.any" or not is_group or group_id != ALLOWED_GROUP_ID or from_bot:
        return {"status": "ok"}

    db = get_session()
    try:
        async with httpx.AsyncClient() as http:
            sender_jid = await lid_resolver.resolve(
                sender_jid_raw, group_id, db, http, WAHA_URL, WAHA_API_KEY, session
            )
            mentions = await lid_resolver.resolve_many(
                mentions_raw, group_id, db, http, WAHA_URL, WAHA_API_KEY, session
            )

        print(
            f"group_id={group_id} sender={sender_jid} (raw={sender_jid_raw!r}, {sender_name!r}) "
            f"from_me={from_me} text={text!r} mentions={mentions} (raw={mentions_raw})"
        )

        resposta = commands.dispatch(text, sender_jid, mentions, db)

        if resposta:
            async with httpx.AsyncClient() as http:
                await reply(http, session, group_id, f"[NicoBot] {resposta}")
    finally:
        db.close()

    return {"status": "ok"}


@app.post("/admin/migrate-jids")
async def migrate_jids(request: Request):
    """Resolve usuários com jid @lid para @c.us usando o LidMap (populado via WAHA).
    Body: {"group_id": "...@g.us", "session": "default"}
    Header: X-Admin-Token: <ADMIN_TOKEN>
    """
    if ADMIN_TOKEN and request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    body = await request.json()
    group_id = body.get("group_id") or ALLOWED_GROUP_ID
    session = body.get("session", "default")
    if not group_id.endswith("@g.us"):
        raise HTTPException(status_code=400, detail="group_id inválido")

    db = get_session()
    try:
        async with httpx.AsyncClient() as http:
            populados = await lid_resolver.populate_from_group(
                group_id, db, http, WAHA_URL, WAHA_API_KEY, session
            )

            usuarios = db.query(Usuario).filter(Usuario.jid.like("%@lid")).all()
            atualizados, nao_resolvidos = [], []
            for u in usuarios:
                novo = await lid_resolver.resolve(
                    u.jid, group_id, db, http, WAHA_URL, WAHA_API_KEY, session
                )
                if novo != u.jid:
                    colidente = db.query(Usuario).filter_by(jid=novo).first()
                    if colidente and colidente.id != u.id:
                        nao_resolvidos.append({"id": u.id, "lid": u.jid, "motivo": f"colisão com id={colidente.id}"})
                        continue
                    antigo = u.jid
                    u.jid = novo
                    atualizados.append({"id": u.id, "de": antigo, "para": novo})
                else:
                    nao_resolvidos.append({"id": u.id, "lid": u.jid, "motivo": "sem mapeamento no LidMap"})
            db.commit()

        return {
            "lid_map_populados": populados,
            "atualizados": atualizados,
            "nao_resolvidos": nao_resolvidos,
        }
    finally:
        db.close()


async def reply(http: httpx.AsyncClient, session: str, chat_id: str, text: str):
    await http.post(
        f"{WAHA_URL}/api/sendText",
        headers={"X-Api-Key": WAHA_API_KEY},
        json={"session": session, "chatId": chat_id, "text": text},
    )
