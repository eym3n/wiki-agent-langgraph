# Wiki-Bot with LangGraph and MCP

This project demonstrates a multi-agent application using [LangGraph](https://langchain-ai.github.io/langgraph/) and [Google Gemini](https://ai.google.dev/), leveraging [wikipedia-mcp](https://github.com/modelcontextprotocol/servers/tree/main/src/wikipedia) for Wikipedia access via the Model Context Protocol (MCP).

It is exposed as a **FastAPI** application with streaming support and SQLite persistence, structured for scalability.

## Prerequisites

- Python 3.12+
- `uv` package manager
- Google Gemini API Key

## Setup

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Environment Variables:**
    Copy `.env.example` to `.env` and add your Google API key.
    ```bash
    cp .env.example .env
    # Edit .env and add GOOGLE_API_KEY=...
    ```

## Usage

Start the server:

```bash
uv run src/main.py
```

The server runs at `http://0.0.0.0:8000`.

### Chat Endpoint

**POST** `/api/v1/chat`

**Payload:**
```json
{
  "message": "Who is the current president of France?",
  "thread_id": "session_1"
}
```

**Response:** Server-Sent Events (SSE) stream.

## Architecture

- **FastAPI**: Handles HTTP requests and streaming.
- **LangGraph**: Manages the agent workflow and state.
- **SQLite**: Persists conversation state (checkpoints).
- **MCP Integration**: Connects to `wikipedia-mcp` via stdio.

## Project Structure

```text
src/
├── main.py             # Application entry point and lifespan management
├── agent/              # LangGraph agent logic
│   ├── graph.py        # Graph construction
│   ├── nodes/          # Agent nodes (LLM logic)
│   ├── prompts/        # Agent prompts
│   ├── state.py        # State definition
│   └── edges.py        # Graph edge logic
├── api/                # API layer
│   ├── routers/        # FastAPI routers
│   └── schemas.py      # Pydantic models
├── core/               # Core utilities
│   └── config.py       # Configuration settings
├── services/           # Business logic
│   └── agent_service.py # Agent lifecycle and MCP connection
└── mcp/                # MCP integration
    └── mcp_client_utils.py # MCP connection helpers
```
