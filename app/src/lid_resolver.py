import re
import httpx
from sqlalchemy.orm import Session

from src.controllers import usuario_lid_controller as ulc


class LidResolver:
    """Resolve identificadores do WhatsApp no telefone canônico (só dígitos).

    Uma instância vale por requisição: agrupa a sessão de banco, o cliente
    HTTP, o grupo em questão e os dados de acesso à WAHA — assim os métodos
    não precisam repassar tudo isso a cada chamada.
    """

    def __init__(
        self,
        db: Session,
        http: httpx.AsyncClient,
        group_id: str | None,
        waha_url: str,
        waha_api_key: str | None,
        waha_session: str,
    ):
        self.db = db
        self.http = http
        self.group_id = group_id
        self.waha_url = waha_url
        self.waha_api_key = waha_api_key
        self.waha_session = waha_session

    # --- helpers de string (sem estado) ---

    @staticmethod
    def is_lid(wa_id: str) -> bool:
        """True se o identificador é um @lid (ID opaco do WhatsApp)."""
        return isinstance(wa_id, str) and wa_id.endswith("@lid")

    @staticmethod
    def so_digitos(valor: str) -> str:
        """Reduz qualquer JID de telefone ao número puro.
        Ex: '5511999@c.us' -> '5511999', '+55 11 99999' -> '5511999'."""
        return re.sub(r"\D", "", valor or "")

    @staticmethod
    def _extrair_ids(participante: dict) -> tuple[str | None, str | None]:
        """Extrai (lid, telefone) de um participante WAHA, tolerando variações
        de schema. O telefone vem normalizado como número puro (só dígitos)."""
        pid = participante.get("id")
        serializado = pid.get("_serialized") if isinstance(pid, dict) else pid

        lid = None
        telefone = participante.get("phoneNumber") or participante.get("pn")

        if isinstance(serializado, str):
            if serializado.endswith("@lid"):
                lid = serializado
            elif serializado.endswith("@c.us") or serializado.endswith("@s.whatsapp.net"):
                telefone = telefone or serializado

        # alguns engines retornam dois campos lado a lado
        alt_lid = participante.get("lid")
        if isinstance(alt_lid, str) and alt_lid.endswith("@lid"):
            lid = lid or alt_lid

        telefone = LidResolver.so_digitos(telefone) if telefone else None
        return lid, (telefone or None)

    # --- WAHA ---

    async def _buscar_participantes(self) -> dict[str, str]:
        """Consulta a WAHA e devolve {lid: telefone} de todos os participantes
        do grupo. Devolve {} se a consulta falhar — o WhatsApp é a única fonte
        de lid -> número."""
        headers = {"X-Api-Key": self.waha_api_key} if self.waha_api_key else {}
        try:
            r = await self.http.get(
                f"{self.waha_url}/api/{self.waha_session}/groups/{self.group_id}/participants",
                headers=headers,
            )
        except httpx.HTTPError:
            return {}
        if r.status_code != 200:
            return {}

        mapa: dict[str, str] = {}
        for p in r.json() or []:
            lid, telefone = self._extrair_ids(p)
            if lid and telefone:
                mapa[lid] = telefone
        return mapa

    # --- cache ---

    async def _garantir_cache(self, lids: list[str]) -> dict[str, str]:
        """Garante que os @lid informados tenham vínculo em cache, consultando
        a WAHA uma única vez se algum estiver faltando. Retorna o {lid: telefone}
        obtido da WAHA, ou {} quando não foi preciso consultar."""
        if not lids or not self.group_id or not self.group_id.endswith("@g.us"):
            return {}
        faltam = [l for l in lids if not ulc.existe_vinculo(self.db, l)]
        if not faltam:
            return {}
        mapa = await self._buscar_participantes()
        ulc.cachear_vinculos(self.db, mapa)
        return mapa

    # --- API pública ---

    async def resolver(self, wa_id: str) -> str:
        """Converte um identificador cru do WhatsApp no telefone canônico.

        - JID de telefone (@c.us / @s.whatsapp.net) -> número puro.
        - @lid -> telefone vinculado (cache UsuarioLid; consulta a WAHA se preciso).
        - @lid que a WAHA não conhece -> retorna o próprio @lid (não resolvido).
        """
        resolvidos = await self.resolver_muitos([wa_id])
        return resolvidos[0]

    async def resolver_muitos(self, wa_ids: list[str]) -> list[str]:
        """Resolve uma lista de identificadores, consultando a WAHA no máximo
        uma vez quando há @lid sem vínculo em cache."""
        if not wa_ids:
            return []

        lids = [w for w in wa_ids if self.is_lid(w)]
        mapa = await self._garantir_cache(lids)

        resolvidos: list[str] = []
        for w in wa_ids:
            if not self.is_lid(w):
                resolvidos.append(self.so_digitos(w))
                continue
            usuario = ulc.get_usuario_por_lid(self.db, w)
            if usuario:
                resolvidos.append(usuario.telefone)
            else:
                resolvidos.append(mapa.get(w) or w)
        return resolvidos
