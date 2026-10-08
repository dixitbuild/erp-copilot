# ERP Copilot

A multi-agent assistant for ERP questions, built with FastAPI and Groq. Every user message goes
through a **guard agent** first; only relevant, clean queries reach the answering agent.

Supported topics: **sales orders**, **purchase orders**, **work orders**.

## Flow

```mermaid
flowchart TD
    U([User]) -->|POST /chat| API[api.py<br/>FastAPI]
    API --> G{Guard agent<br/>agents/guard.py}
    G -->|injection detected| B1[Blocked:<br/>manipulation message]
    G -->|not about sales / purchase / work orders| B2[Blocked:<br/>ask a relevant question]
    G -->|guard output unusable| B2
    G -->|relevant and clean| E[ERP agent<br/>agents/erp.py]
    E <-->|tool calls| M[MCP DB server<br/>mcp_servers/db_server.py]
    M --> DB[(SQLite erp.db<br/>read-only)]
    E --> L[llm.py]
    G -.-> L
    L <--> GQ[(Groq API)]
    E --> R([Reply, blocked=false])
    B1 --> RB([Reply, blocked=true])
    B2 --> RB
```

The guard fails closed: if its output cannot be parsed, the message is blocked.

## Project structure

```
erp-copilot/
├── pyproject.toml
├── .env.example
└── src/erp_copilot/
    ├── __init__.py      # entry point: starts the server
    ├── config.py        # settings from .env
    ├── llm.py           # Groq client and chat_completion()
    ├── api.py           # FastAPI app: /health, /chat
    ├── schemas.py       # Pydantic models: SalesOrder, PurchaseOrder, WorkOrder
    ├── dummy_data.py    # sample orders (seeds the database)
    ├── db.py            # SQLite setup + read-only, table-restricted queries
    ├── mcp_client.py    # starts an MCP server, exposes its tools to Groq
    ├── routers/
    │   └── orders.py    # GET /sales-orders, /purchase-orders, /work-orders
    ├── mcp_servers/
    │   └── db_server.py # MCP tools: describe_table, run_query
    └── agents/
        ├── base.py      # Agent class (run, run_with_tools)
        ├── guard.py     # relevance + prompt-injection check
        └── erp.py       # ERP agent: schema summary prompt + DB tools
```

Layers: `api.py` → `agents/` → `llm.py` → Groq. `config.py` is used by all.

## Setup

```bash
cp .env.example .env     # then set GROQ_API_KEY
uv sync
```

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | required | Groq credentials |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model used by all agents |
| `GROQ_TEMPERATURE` | `0.7` | Default temperature (guard uses 0) |

## Run

```bash
uv run erp-copilot
# or
uv run uvicorn erp_copilot.api:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

## API

### `GET /health`
Returns `{"status": "ok"}`.

### `POST /chat`

Request (`message` is 1 to 2000 characters):
```json
{"message": "What is the status of sales order SO-1001?"}
```

Response:
```json
{"agent": "erp", "blocked": false, "reply": "..."}
```

| Case | `agent` | `blocked` | `reply` |
|---|---|---|---|
| Relevant query | `erp` | `false` | Answer from the ERP agent |
| Off-topic query | `guard` | `true` | Asks for a relevant question |
| Injection attempt | `guard` | `true` | Says the message was blocked |

### Order endpoints (dummy data)

| Endpoint | Returns |
|---|---|
| `GET /sales-orders`, `/purchase-orders`, `/work-orders` | List, with optional `?status=` filter |
| `GET /sales-orders/{id}` (same for the others) | One order, or `404` |

Errors: `422` for invalid input, `502` if Groq fails.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a purchase order for 50 units"}'
```

## ERP agent and the DB MCP server

The ERP agent answers by querying a SQLite database (`erp.db`, created and seeded from the dummy
data on first start, git-ignored) through an MCP server that the API starts at startup.

- **Prompt:** a curated schema summary (tables, column meanings, business rules, example
  question-to-SQL pairs) lives in `agents/erp.py`.
- **`run_query(sql)`:** a single read-only `SELECT`, max 100 rows. Writes, multiple statements
  and `PRAGMA` are rejected, and a SQLite authorizer blocks any table outside the allow-list.
- **`describe_table(table)`:** fallback for column details the prompt does not cover. Allowed
  tables come from `ERP_ALLOWED_TABLES` (default: the three order tables), so a different role can
  be given a smaller set.

## Roadmap

- Second MCP server wrapping the order GET endpoints (API data fetch)
- Orchestrator that routes relevant queries to specialist agents (sales, purchase, work orders)
- Tests with a mocked Groq client
- Streaming responses
