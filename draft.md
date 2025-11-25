# Customer Support Agent (CSA)

A simple CLI-based chatbot for customer support using Google ADK and MCP Toolbox.

## Features

- Interactive CLI interface for customer support
- Order status lookup by Order ID
- Find all orders for a specific customer
- Auto-normalizes Order IDs (e.g., '101' → 'ORD-101')
- Auto-normalizes Customer IDs (e.g., '001' → 'CUST-001')
- Persistent conversation history within a session

## Prerequisites

- Python 3.13+
- MCP Toolbox running on `http://127.0.0.1:5000`
- PostgreSQL database with customer orders (configured in `mcp_toolbox/tools.yaml`)

## Installation

### Spinning the Docker


```bash
docker run --name some-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql \
  -d postgres
```
### execute postgres on terminal (Optional)
```bash
# execute postgres on terminal
docker exec -it some-postgres psql -U postgres
```

## 🏪✨ Sample Synthetic Customer Order Data

Below is a quick-start SQL snippet to create and populate your `customer_orders` table with realistic demo data for testing the customer support agent!

<details>
<summary><strong>Show SQL (click to expand)</strong></summary>

```sql
-- 📦 Create customer_orders table
CREATE TABLE customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(100) NOT NULL, 
    status VARCHAR(20) CHECK (status IN ('PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED')),
    items JSONB,
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount DECIMAL(10, 2)
);

-- 🛒 Insert demo customer orders
INSERT INTO customer_orders (customer_email, status, items, order_date, total_amount) VALUES
('alice.jones@example.com', 'DELIVERED', '[{"product": "Ergonomic Office Chair", "qty": 1, "price": 250.00}]', NOW() - INTERVAL '6 months', 250.00),
('alice.jones@example.com', 'DELIVERED', '[{"product": "Wireless Mouse", "qty": 1, "price": 25.00}, {"product": "Mouse Pad", "qty": 1, "price": 10.00}]', NOW() - INTERVAL '3 months', 35.00),
('alice.jones@example.com', 'SHIPPED', '[{"product": "Mechanical Keyboard", "qty": 1, "price": 120.00}]', NOW() - INTERVAL '2 days', 120.00),
('alice.jones@example.com', 'PROCESSING', '[{"product": "USB-C Hub", "qty": 1, "price": 45.00}]', NOW() - INTERVAL '1 hour', 45.00),

('bob.smith@techmail.com', 'DELIVERED', '[{"product": "Gaming Laptop 15-inch", "qty": 1, "price": 1500.00}, {"product": "Laptop Stand", "qty": 1, "price": 50.00}]', NOW() - INTERVAL '1 year', 1550.00),
('bob.smith@techmail.com', 'CANCELLED', '[{"product": "VR Headset", "qty": 1, "price": 400.00}]', NOW() - INTERVAL '10 days', 400.00),
('bob.smith@techmail.com', 'PROCESSING', '[{"product": "Curved Monitor 34-inch", "qty": 1, "price": 450.00}]', NOW() - INTERVAL '4 hours', 450.00),

('charlie.d@webmail.com', 'DELIVERED', '[{"product": "AA Batteries (Pack of 12)", "qty": 2, "price": 15.00}]', NOW() - INTERVAL '45 days', 30.00),
('charlie.d@webmail.com', 'DELIVERED', '[{"product": "HDMI Cable 6ft", "qty": 3, "price": 8.00}]', NOW() - INTERVAL '20 days', 24.00),

('diana.prince@hero.net', 'DELIVERED', '[{"product": "Smart Watch Gen 5", "qty": 1, "price": 299.00}]', NOW() - INTERVAL '60 days', 299.00),
('diana.prince@hero.net', 'RETURNED', '[{"product": "Running Shoes", "qty": 1, "price": 120.00}]', NOW() - INTERVAL '15 days', 120.00),

('evan.g@bizcorp.com', 'SHIPPED', '[{"product": "Office Desk", "qty": 2, "price": 300.00}, {"product": "Filing Cabinet", "qty": 2, "price": 150.00}]', NOW() - INTERVAL '1 day', 900.00),

('fiona.shrek@swamp.com', 'CANCELLED', '[{"product": "Skincare Gift Set", "qty": 1, "price": 85.00}]', NOW() - INTERVAL '5 days', 85.00),

('george.j@jungle.com', 'PROCESSING', '[{"product": "Bluetooth Speaker", "qty": 1, "price": 60.00}]', NOW() - INTERVAL '30 minutes', 60.00),

('hannah.m@school.edu', 'DELIVERED', '[{"product": "Notebook Pack", "qty": 5, "price": 12.00}, {"product": "Gel Pens", "qty": 2, "price": 5.00}]', NOW() - INTERVAL '4 months', 70.00),

('ian.malcolm@chaos.com', 'DELIVERED', '[{"product": "Professional Camera Lens", "qty": 1, "price": 2200.00}]', NOW() - INTERVAL '8 months', 2200.00),

('julia.child@kitchen.com', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '3 months', 25.00),
('julia.child@kitchen.com', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '2 months', 25.00),
('julia.child@kitchen.com', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '1 month', 25.00),
('julia.child@kitchen.com', 'PROCESSING', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}, {"product": "Descaling Kit", "qty": 1, "price": 15.00}]', NOW() - INTERVAL '3 hours', 40.00);
```

</details>


```bash
# Install dependencies using uv
uv sync
```

## Usage

### Running the Chatbot

```bash
# Run the CLI chatbot
uv run python chatbot.py

# Or alternatively
uv run chatbot.py
```
### Running using adk web

```bash
# run the toolbox in terminal 1
cd mcp_toolbox
./toolbox --tools-file tools.yaml --ui

# run the toolbox in terminal 2
adk web
```


## Project Structure

```
CSA/
├── chatbot.py              # Main entry point
├── cs_agent/
│   ├── __init__.py
│   ├── agent.py           # Agent definition (Google ADK)
│   └── cli.py             # CLI interface with Runner
├── mcp_toolbox/           # MCP Toolbox tools
│   ├── toolbox.exe
│   └── tools.yaml         # Tool definitions
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## How It Works

1. **Agent**: Defined in `cs_agent/agent.py` using Google ADK's `Agent` class with Gemini 2.5 Flash model
2. **Runner**: The CLI uses Google ADK's `Runner` with `InMemorySessionService` for session management
3. **Tools**: MCP Toolbox provides database tools for querying customer orders
4. **Session**: Maintains conversation context throughout the chat session

## Agent Capabilities

The customer support agent can:
- Get order status using `get-order-status` tool
- Find customer orders using `find-customer-orders` tool
- Automatically format Order IDs and Customer IDs
- Provide friendly, professional customer support
- Maintain conversation context across multiple queries

## Tools Configuration

The agent uses tools defined in `mcp_toolbox/tools.yaml` under the toolset `cs_agent_tools`:

- **get-order-status**: Retrieves order details by Order ID
- **find-customer-orders**: Finds all orders for a given Customer ID

## Troubleshooting

**Error: Connection refused to http://127.0.0.1:5000**
- Ensure MCP Toolbox is running: `cd mcp_toolbox && ./toolbox.exe`

**Error: Database connection failed**
- Check PostgreSQL is running
- Verify credentials in `mcp_toolbox/tools.yaml`

**Unclosed client session warnings**
- These are expected and can be safely ignored


### Resources 
MCP Tool Box Colab Notebook [https://colab.research.google.com/github/googleapis/genai-toolbox/blob/main/docs/en/getting-started/colab_quickstart.ipynb#scrollTo=QqRlWqvYNKSo]
Google ADK [https://google.github.io/adk-docs/]



