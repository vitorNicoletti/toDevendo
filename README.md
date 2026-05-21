# toDevendo

Bot de WhatsApp para registrar e controlar dívidas dentro de um grupo confiavel de amigos. Os
membros usam comandos de texto (`!deve`, `!devo`, `!pago`, etc.) e o bot
responde no próprio grupo, guardando tudo num banco MySQL.

## Como funciona

O projeto roda em três contêineres Docker:

- **waha** — gateway [WAHA](https://waha.devlike.pro/) que conecta ao WhatsApp
  e envia os eventos de mensagem para a aplicação via webhook.
- **to-devendo** — aplicação [FastAPI](https://fastapi.tiangolo.com/) que
  recebe os webhooks, interpreta os comandos e responde.
- **db** — banco MySQL 8.0 que persiste usuários e dívidas.

Fluxo de uma mensagem:

```
WhatsApp → WAHA → POST /webhook → commands.dispatch() → resposta → WAHA → WhatsApp
```

O bot só responde mensagens do grupo definido em `ALLOWED_GROUP_IDS` e ignora
as mensagens enviadas por ele mesmo (prefixadas com `[NicoBot]`).

## Comandos do bot

| Comando | Descrição |
|---------|-----------|
| `!ajuda` | Mostra a lista de comandos |
| `!cadastro <nome>` | Cadastra você no sistema |
| `!pix` | Mostra sua chave Pix |
| `!pix @pessoa` | Mostra a chave Pix de alguém |
| `!pix -save <chave>` | Salva sua chave Pix |
| `!deve <valor> @pessoa <descrição>` | Registra que alguém te deve |
| `!devo <valor> @pessoa <descrição>` | Registra que você deve a alguém |
| `!deve` | Lista o que te devem |
| `!devo` | Lista o que você deve |
| `!pago <id>` | Marca uma dívida como paga |
| `!cancelar <id>` | Cancela uma dívida que você registrou |

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose
- Uma conta de WhatsApp para escanear o QR Code

## Configuração

1. Clone o repositório.

2. Crie o arquivo `.env` a partir do exemplo e preencha os valores:

   ```bash
   cp .env.example .env
   ```

   | Variável | Descrição |
   |----------|-----------|
   | `WAHA_PORT` | Porta exposta do WAHA (padrão `3000`) |
   | `MYSQL_ROOT_PASSWORD` | Senha do usuário root do MySQL |
   | `MYSQL_USER` | Usuário da aplicação no MySQL |
   | `MYSQL_PASSWORD` | Senha do usuário da aplicação |
   | `WAHA_API_KEY` | Chave secreta da API do WAHA |
   | `ALLOWED_GROUP_IDS` | ID do grupo autorizado (`...@g.us`) |
   | `BOT_NAME` | Nome do bot, prefixo das mensagens (padrão `NicoBot`) |

3. Suba os contêineres:

   ```bash
   docker compose up --build
   ```

4. Escaneie o QR Code do WhatsApp. Ele é impresso no log do contêiner `waha`
   (`WAHA_PRINT_QR=True`).

## Estrutura do projeto

```
.
├── docker-compose.yaml      # Orquestra waha, app e banco
├── schemaBanco.sql          # DDL inicial do banco (rodado no primeiro boot)
├── .env.example             # Modelo das variáveis de ambiente
└── app/
    ├── Dockerfile
    ├── main.py              # Conecta ao WhatsApp e sobe o servidor
    ├── requirements.txt
    └── src/
        ├── app.py           # Rota FastAPI /webhook
        ├── commands.py      # Interpreta e despacha os comandos do bot
        ├── database.py      # Sessão do SQLAlchemy
        ├── create_wpp_connection.py
        ├── controllers/     # Regras de negócio (usuário, dívida)
        ├── models/          # Modelos SQLAlchemy
        └── views/           # Formatação das mensagens de resposta
```

## Banco de dados

O schema é criado automaticamente no primeiro boot a partir de
[schemaBanco.sql](schemaBanco.sql). Tabelas principais:

- **Usuario** — membros cadastrados, identificados pelo `jid` (o identificador
  do WhatsApp — `@lid` ou `@c.us` — exatamente como chega no webhook).
- **Divida** — dívidas entre usuários (devedor, credor, valor, status).

O `jid` é usado direto, sem tradução: cada pessoa é identificada pelo mesmo
identificador que o WhatsApp envia em toda mensagem dela.

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/webhook` | Recebe os eventos de mensagem do WAHA |

## Testes

Os testes unitários ficam em [app/tests/](app/tests/) e usam um banco SQLite
em memória — não precisam de Docker nem do MySQL.

```bash
cd app
pip install -r requirements-dev.txt
pytest
```

## Notas de segurança

- O arquivo `.env` contém segredos e **não deve** ser versionado — já está no
  `.gitignore`.
- As pastas `mysql_data/` (dados do banco) e `.sessions/` (sessão do WhatsApp)
  também são ignoradas pelo Git.
