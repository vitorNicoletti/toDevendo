from collections import OrderedDict

from fastapi import FastAPI, Request
import httpx
import os

from src.database import get_session
from src import commands

app = FastAPI()

WAHA_URL = os.getenv("WAHA_URL", "http://waha:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_IDS", "naovaiacharnada")
BOT_NAME = os.getenv("BOT_NAME", "NicoBot")
BOT_TAG = f"[{BOT_NAME}]"

# Idempotência: a WAHA reentrega o mesmo webhook quando o handler demora a
# responder. Guardamos os IDs já processados (janela curta, em memória) para
# não responder duas vezes à mesma mensagem.
_MAX_IDS_PROCESSADOS = 500
_ids_processados: "OrderedDict[str, None]" = OrderedDict()


def _id_da_mensagem(payload: dict) -> str | None:
    """Extrai o ID único da mensagem, tolerando variações de schema da WAHA."""
    mid = payload.get("id")
    if isinstance(mid, dict):
        mid = mid.get("_serialized")
    return mid if isinstance(mid, str) and mid else None


def _ja_processada(msg_id: str | None) -> bool:
    """True se esta mensagem já foi processada (reentrega da WAHA).
    Sem ID, não há como deduplicar — trata como nova."""
    if not msg_id:
        return False
    if msg_id in _ids_processados:
        return True
    _ids_processados[msg_id] = None
    if len(_ids_processados) > _MAX_IDS_PROCESSADOS:
        _ids_processados.popitem(last=False)
    return False


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

    # identificador do WhatsApp de quem enviou (@lid ou @c.us) — usado direto
    remetente_jid = payload.get("participant") or from_id
    remetente_nome = payload.get("_data", {}).get("notifyName", "")

    from_bot = text.startswith(BOT_TAG)
    mencionados = payload.get("_data", {}).get("mentionedJidList", [])

    if event != "message.any" or not is_group or group_id != ALLOWED_GROUP_ID or from_bot:
        return {"status": "ok"}

    # ignora reentregas do mesmo webhook (precisa vir antes de qualquer await)
    if _ja_processada(_id_da_mensagem(payload)):
        return {"status": "ok"}

    db = get_session()
    try:
        print(
            f"group_id={group_id} remetente={remetente_jid} ({remetente_nome!r}) "
            f"from_me={from_me} text={text!r} mencionados={mencionados}"
        )

        resposta = commands.dispatch(text, remetente_jid, mencionados, db)

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
