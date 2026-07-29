# Arquitetura — Precificador

Documento da arquitetura e da stack tecnológica do projeto **Precificador**, focado em integrar Tiny ERP e Mercado Livre para automação de precificação e promoções.

## Visão geral

O sistema é uma **API REST** (FastAPI) que autentica contas via OAuth, persiste tokens e expõe endpoints para consultar produtos (Tiny) e anúncios/preços (Mercado Livre). Um console **Streamlit** local consome essa API para testes manuais, sem ir para a VPS.

Objetivo de negócio (em evolução): cruzar produtos do Tiny com publicações do ML pelo SKU e aplicar promoções tradicionais.

```text
                    ┌─────────────────────┐
                    │  Streamlit (local)  │
                    │  tools/streamlit    │
                    └──────────┬──────────┘
                               │ HTTP + X-Internal-Token
                               ▼
┌──────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│  Tiny ERP    │◄──►│  FastAPI (backend)  │◄──►│  Mercado Livre   │
│  OAuth + API │    │  precificador-auth  │    │  OAuth + API     │
└──────────────┘    └──────────┬──────────┘    └──────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  PostgreSQL         │
                    │  oauth_connections  │
                    │  oauth_states       │
                    └─────────────────────┘
```

## Stack tecnológica

| Camada | Tecnologia | Uso |
|--------|------------|-----|
| API | **Python 3.12**, **FastAPI**, **Uvicorn** | Servidor HTTP e rotas REST |
| ORM / DB | **SQLAlchemy**, **psycopg** | Persistência e sessão PostgreSQL |
| Banco | **PostgreSQL** (`DATABASE_URL`) | Tokens OAuth e estados PKCE |
| Integrações | HTTP (APIs externas) | Tiny ERP e Mercado Livre |
| Auth apps | **OAuth 2.0 + PKCE** | Login Tiny e ML por empresa |
| Jobs internos | Header `X-Internal-Token` | Refresh de tokens e rotas protegidas |
| Container | **Docker**, **Docker Compose** | Deploy da API (`auth-api` na porta 8000) |
| UI de teste | **Streamlit**, **httpx**, **pandas** | Console local contra a API |
| Scripts | Bash (`scripts/`) | Refresh agendado de tokens (ex.: ML SP) |

## Estrutura de pastas

```text
precificador/
├── backend/                 # Aplicação principal (API)
│   ├── main.py              # App FastAPI e registro de routers
│   ├── db.py                # Engine / SessionLocal / Base
│   ├── models.py            # Modelos ORM
│   ├── api/
│   │   ├── dependencies.py  # Injeção de sessão DB
│   │   └── routes/          # Endpoints HTTP
│   ├── services/            # Regras e clientes de API externa
│   ├── repositories/        # Acesso a dados OAuth
│   ├── constants/           # Empresas e provedores
│   └── core/                # Startup (create_all das tabelas)
├── tools/streamlit/         # Console de testes (não vai para VPS)
├── scripts/                 # Jobs de manutenção (refresh tokens)
├── config/                  # Placeholder de configurações
├── docker-compose.yml
├── Dockerfile
└── briefing.md              # Requisitos de promoções ML
```

## Camadas da API

Arquitetura em camadas, com responsabilidades separadas:

```text
Routes (api/routes)
    → Services (oauth_*, ml_api, tiny_erp_api, health)
        → Repositories (oauth_connection, oauth_state)
            → Models / PostgreSQL
```

| Camada | Responsabilidade |
|--------|------------------|
| **Routes** | HTTP, query params, headers, status codes |
| **Services** | OAuth (PKCE, exchange, refresh), chamadas Tiny/ML |
| **Repositories** | CRUD de conexões e estados OAuth |
| **Models** | Schema das tabelas |
| **Dependencies** | Sessão SQLAlchemy por request |

### Multi-empresa e multi-provedor

Contexto atual:

- Empresas: `SP`, `SC`
- Provedores: `ml`, `tiny`

Cada conexão OAuth é única por `(company_code, provider)`.

## Domínio de dados (atual)

### `oauth_connections`

Armazena tokens ativos por empresa/provedor (`access_token`, `refresh_token`, `expires_at`, etc.).

### `oauth_states`

Estados OAuth temporários (PKCE `code_verifier`, expiração, uso único) para o fluxo de autorização.

> Tabelas futuras previstas pelo briefing: mapeamento local `SELLER_ID + SKU + ITEM_ID + VARIATION_ID` para cruzamento Tiny ↔ Mercado Livre.

## Superfície da API (atual)

| Prefixo | Função |
|---------|--------|
| `GET /health` | Saúde do serviço |
| `/oauth/tiny/*` | Start, callback e refresh Tiny |
| `/oauth/ml/*` | Start, callback e refresh Mercado Livre |
| `/tiny/produtos` | Listagem de produtos Tiny |
| `/tiny/ordens-compra` | Ordens de compra Tiny |
| `/ml/me` | Perfil da conta ML |
| `/ml/items/search` | Busca de anúncios do vendedor |
| `/ml/items/{id}` | Detalhe do anúncio |
| `/ml/items/{id}/prices` | Preços do item |
| `/ml/items/{id}/sale_price` | Preço de venda efetivo |

Rotas de integração sensíveis exigem `X-Internal-Token` (mesmo valor de `INTERNAL_JOB_TOKEN`).

## Deploy

- Imagem: `python:3.12-slim`
- Processo: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- Compose: serviço `auth-api`, porta `127.0.0.1:8000:8000`
- Variáveis: `DATABASE_URL`, credenciais OAuth Tiny/ML por empresa, `INTERNAL_JOB_TOKEN`

No startup, a API cria as tabelas ORM se o banco estiver configurado (`Base.metadata.create_all`).

## Ferramentas auxiliares

- **Streamlit** (`tools/streamlit`): UI local que chama a API em produção/remoto via `API_BASE_URL` + token interno.
- **Script** `scripts/refresh_ml_sp.sh`: refresh periódico do token ML da empresa SP via curl.

## Fluxo de negócio alvo (promoções)

Direção definida no `briefing.md` (ainda em construção na API):

```text
SKU Tiny → SELLER_SKU ML → ITEM_ID (MLB...) → campanha / deal_price
```

Etapas previstas:

1. Autenticar ML e obter `SELLER_ID`
2. Listar anúncios e mapear SKU → `ITEM_ID` (+ `VARIATION_ID` quando houver)
3. Criar campanha do vendedor (`SELLER_CAMPAIGN`)
4. Filtrar candidatos elegíveis
5. Calcular `deal_price` e adicionar itens à promoção
6. Confirmar preço exibido e registrar resultados/erros

Limitação relevante: a promoção aplica-se ao `ITEM_ID`, não à variação isolada.

## Princípios de evolução

- Mudanças pequenas e incrementais
- Manter separação routes / services / repositories
- Tipagem e clareza Python (PEP 8)
- Prova de conceito com poucos produtos antes de processamento em lote
