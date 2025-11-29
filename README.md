# Wiki-Bot with LangGraph and MCP

A multi-agent Wikipedia research assistant using [LangGraph](https://langchain-ai.github.io/langgraph/) and [Ollama](https://ollama.ai/), leveraging [wikipedia-mcp](https://github.com/modelcontextprotocol/servers/tree/main/src/wikipedia) for Wikipedia access via the Model Context Protocol (MCP).

Exposed as a **FastAPI** application with streaming support and SQLite persistence.

## Prerequisites

- Python 3.12+
- `uv` package manager
- [Ollama](https://ollama.ai/) installed and running

## Setup

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Pull the Ollama Model:**
    ```bash
    ollama pull PetrosStav/gemma3-tools:4b
    ```

3.  **Environment Variables (Optional):**
    Create a `.env` file to customize settings:
    ```bash
    OLLAMA_MODEL=PetrosStav/gemma3-tools:4b
    OLLAMA_BASE_URL=http://localhost:11434
    HOST=0.0.0.0
    PORT=8000
    ```

## Usage

Start the server:

```bash
uv run uvicorn src.main:app --reload
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

**Response:** Server-Sent Events (SSE) stream with routing info, tool calls, content, and Wikipedia references.

**Example Events:**
```
data: {"router": "context"}
data: {"tool": "search_wikipedia"}
data: {"tool": "get_summary", "references": ["https://en.wikipedia.org/wiki/Emmanuel_Macron"]}
data: {"content": "Emmanuel Macron is the current president of France..."}
data: {"references": ["https://en.wikipedia.org/wiki/Emmanuel_Macron"]}
data: [DONE]
```

## Architecture

- **FastAPI**: Handles HTTP requests and SSE streaming.
- **LangGraph**: Manages the multi-agent workflow and state.
- **Ollama**: Local LLM inference.
- **SQLite**: Persists conversation state (checkpoints).
- **MCP Integration**: Connects to `wikipedia-mcp` via stdio.

## Agent Flow

1. **Router Node**: Determines if the query needs Wikipedia research (`context`) or a quick reply (`reply`).
2. **Context Node**: Searches Wikipedia using MCP tools, gathers relevant articles.
3. **Synthesize Node**: Produces a comprehensive answer with article snapshots and references.
4. **Reply Node**: Handles conversational queries that don't require research.

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
