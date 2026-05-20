from fastapi import FastAPI, Request
import httpx
import os

from src.database import get_session
from src import commands
from src.lid_resolver import LidResolver

app = FastAPI()

WAHA_URL = os.getenv("WAHA_URL", "http://waha:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_IDS", "naovaiacharnada")
BOT_NAME = os.getenv("BOT_NAME", "NicoBot")
BOT_TAG = f"[{BOT_NAME}]"


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

    remetente_wa_id = payload.get("participant") or from_id
    remetente_nome = payload.get("_data", {}).get("notifyName", "")

    from_bot = text.startswith(BOT_TAG)
    mencionados_wa_id = payload.get("_data", {}).get("mentionedJidList", [])

    if event != "message.any" or not is_group or group_id != ALLOWED_GROUP_ID or from_bot:
        return {"status": "ok"}

    db = get_session()
    try:
        async with httpx.AsyncClient() as http:
            resolver = LidResolver(db, http, group_id, WAHA_URL, WAHA_API_KEY, session)
            remetente_tel = await resolver.resolver(remetente_wa_id)
            mencionados_tel = await resolver.resolver_muitos(mencionados_wa_id)

        print(
            f"group_id={group_id} remetente={remetente_tel} "
            f"(wa_id={remetente_wa_id!r}, {remetente_nome!r}) "
            f"from_me={from_me} text={text!r} mencionados={mencionados_tel}"
        )

        resposta = commands.dispatch(text, remetente_tel, mencionados_tel, db)

        if resposta:
            async with httpx.AsyncClient() as http:
                await reply(http, session, group_id, f"{BOT_TAG} {resposta}")
    finally:
        db.close()

    return {"status": "ok"}


async def reply(http: httpx.AsyncClient, session: str, chat_id: str, text: str):
    await http.post(
        f"{WAHA_URL}/api/sendText",
        headers={"X-Api-Key": WAHA_API_KEY},
        json={"session": session, "chatId": chat_id, "text": text},
    )
