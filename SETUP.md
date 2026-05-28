# Customer Support Agent - Setup & Run Guide

## Project Overview

This project is an AI-powered **Customer Support Agent** built with Google ADK (Agent Development Kit). It uses Gemini 2.5 Flash to help users with order-related queries, featuring memory persistence via Mem0 and full observability via Weights & Biases Weave.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.13+ |
| **Docker** | PostgreSQL container running on port 5432 |
| **W&B Account** | For Weave observability (free at https://wandb.ai) |
| **API Keys** | Google Gemini, Mem0, W&B (see below) |

---

## 1. API Keys Setup

### Get Your Keys

| Service | Where to Get It |
|---------|----------------|
| **Google Gemini** | https://aistudio.google.com/apikey |
| **Mem0** | https://app.mem0.ai/ |
| **Weights & Biases** | https://wandb.ai/authorize |

### Configure `.env`

Edit `cs_agent/.env` and add your keys:

```env
# Google Gemini API key
GOOGLE_API_KEY=your-google-api-key-here

# Mem0 API key for memory persistence
MEM0_API_KEY=your-mem0-api-key-here

# Weights & Biases API key for Weave observability
WANDB_API_KEY=your-wandb-api-key-here
```

---

## 2. PostgreSQL Database Setup

### Start PostgreSQL via Docker

```bash
docker run -d \
  --name some-postgres \
  -e POSTGRES_USER=toolbox_user \
  -e POSTGRES_DB=toolbox_db \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  postgres:latest
```

### Create the `customer_orders` Table

Connect and create the table:

```bash
docker exec -it some-postgres psql -U toolbox_user -d toolbox_db
```

```sql
CREATE TABLE customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT NOW(),
    total_amount DECIMAL(10,2) NOT NULL,
    items TEXT NOT NULL
);

-- Sample data
INSERT INTO customer_orders (customer_email, status, order_date, total_amount, items)
VALUES
    ('alice.jones@example.com', 'Shipped', '2025-05-15', 149.99, '["Wireless Mouse", "USB-C Hub"]'),
    ('alice.jones@example.com', 'Delivered', '2025-04-20', 89.50, '["Notebook Set"]'),
    ('bob.smith@example.com', 'Processing', '2025-05-22', 299.99, '["Mechanical Keyboard"]'),
    ('carol.davis@example.com', 'Delivered', '2025-05-10', 549.99, '["Monitor 27\""]'),
    ('carol.davis@example.com', 'Cancelled', '2025-05-01', 29.99, '["Mouse Pad"]');
```

Type `\q` to exit psql.

---

## 3. Toolbox Configuration

### `mcp_toolbox/tools.yaml`

This file defines the PostgreSQL connection and tools. Ensure the password matches your Docker setup:

```yaml
kind: source
name: customer_db
type: postgres
host: 127.0.0.1
port: 5432
database: toolbox_db
user: toolbox_user
password: mysecretpassword
---
kind: tool
name: get-order-status
type: postgres-sql
source: customer_db
description: Retrieves the full details (status, items, date, total) for a specific Order ID.
parameters:
  - name: order_id
    type: integer
    description: The numeric order identifier.
statement: SELECT status, order_date, total_amount, items FROM customer_orders WHERE order_id = $1;
---
kind: tool
name: find-customer-orders
type: postgres-sql
source: customer_db
description: Finds order history for a customer using their email.
parameters:
  - name: customer_email
    type: string
    description: The customer email address.
statement: SELECT order_id, status, order_date, total_amount, items FROM customer_orders WHERE customer_email = $1 ORDER BY order_date DESC;
---
kind: toolset
name: cs_agent_tools
tools:
  - get-order-status
  - find-customer-orders
```

---

## 4. Running the Application

You need **two terminals**: one for the toolbox server, one for the agent CLI.

### Terminal 1 — Start the Toolbox Server

```bash
cd /c/Work/Customer-Support-Agent/mcp_toolbox
./toolbox.exe --config "tools.yaml" --enable-api
```

Expected output:
```
INFO "Initialized 1 sources: customer_db"
INFO "Initialized 2 tools: get-order-status, find-customer-orders"
INFO "Initialized 2 toolsets: default, cs_agent_tools"
INFO "Server ready to serve!"
```

> **Note:** `--enable-api` is required because the `toolbox_core` Python library still uses the legacy `/api/` endpoints.

### Terminal 2 — Run the Agent

```bash
cd /c/Work/Customer-Support-Agent/cs_agent
uv run python agent_cli.py
```

Example interaction:
```
================================================================================
You: Hi
Agent: Hello! Thank you for contacting customer support. How may I help you today?

================================================================================
You: Check order #5
Agent: Let me look up order #5 for you...
```

Type `quit`, `exit`, `bye`, or `q` to end the session.

---

## 5. Observability with Weave

### What's Traced

Weave automatically captures traces for every agent interaction:

```
main()                          ← Full chat session
  └── run_agent("user message")  ← Each user turn
        ├── [Gemini LLM call]    ← Auto-traced by Weave
        ├── search_memory()      ← Memory retrieval
        ├── get-order-status()   ← Toolbox DB query (if called)
        └── find-customer-orders() ← Toolbox DB query (if called)
  └── save_memory()              ← Memory persistence
```

### View Traces

1. Go to https://wandb.ai/ and log in
2. Select the **"customer-support-agent"** project
3. Click the **Weave** tab to see trace timelines
4. Click any trace to inspect inputs, outputs, and duration

### What You Can Share for Your Assignment

| Option | Description |
|--------|-------------|
| **Trace of a successful tool call** | Ask the agent "Check order #5" — shows `get-order-status` being called |
| **Comparison dashboard** | Run the agent multiple times and compare traces in Weave |
| **Agent using MCP tools** | The toolbox serves tools via MCP protocol (the `/mcp` endpoint) |

---

## 6. Troubleshooting

### Toolbox won't start
```
ERROR "unable to initialize source: failed to connect"
```
- Make sure PostgreSQL Docker container is running: `docker ps`
- Check password in `tools.yaml` matches `POSTGRES_PASSWORD`

### Port 5000 already in use
```bash
taskkill //F //IM toolbox.exe
```

### "Session is closed" or "attached to a different loop"
This was a known bug in earlier versions. The fix was to use `ToolboxSyncClient` instead of `ToolboxClient` (async), since the ADK runner calls tools from a background thread with its own event loop.

### Gemini 503 error
```
google.genai.errors.ServerError: 503 UNAVAILABLE
```
The model is experiencing high demand. Just wait a moment and try again.

### Weave asks for API key interactively
Make sure `WANDB_API_KEY` is set in your `.env` file. The code reads it automatically:

```python
load_dotenv()
wandb_key = os.getenv("WANDB_API_KEY")
if wandb_key:
    os.environ["WANDB_API_KEY"] = wandb_key
weave.init("customer-support-agent")
```

---

## 7. Project Structure

```
cs_agent/
├── .env                  # API keys (GOOGLE_API_KEY, MEM0_API_KEY, WANDB_API_KEY)
├── __init__.py           # Package marker
├── agent.py              # Reference agent config (alternative)
├── agent_cli.ipynb       # Jupyter notebook version
├── agent_cli.py          # ★ Main agent CLI with Weave tracing
├── memory.py             # Memory persistence via Mem0 (with Weave tracing)
├── prompts.py            # Agent system prompts
├── SETUP.md              # ← This file

mcp_toolbox/
├── toolbox.exe           # Toolbox server binary
├── tools.yaml            # Tool definitions & PostgreSQL config
```

---

## 8. Packages Installed

Key dependencies (installed via `uv`):

| Package | Usage |
|---------|-------|
| `google-adk` | Google Agent Development Kit |
| `google-genai` | Gemini LLM access |
| `toolbox-core` | Toolbox client library |
| `mem0ai` | Memory persistence |
| `weave` | W&B Observability |
| `python-dotenv` | Environment variable management |
| `aiohttp` | Async HTTP (used by toolbox client) |
