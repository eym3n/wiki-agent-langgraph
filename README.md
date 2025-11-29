# Wiki-Bot with LangGraph and MCP

A multi-agent Wikipedia research assistant using [LangGraph](https://langchain-ai.github.io/langgraph/) and [Groq](https://groq.com/), leveraging [wikipedia-mcp](https://github.com/modelcontextprotocol/servers/tree/main/src/wikipedia) for Wikipedia access via the Model Context Protocol (MCP).

Exposed as a **FastAPI** application with streaming support and SQLite persistence.

## Prerequisites

- Python 3.12+
- `uv` package manager
- [Groq API Key](https://console.groq.com/) **OR** [Ollama](https://ollama.ai/) installed locally

## Setup

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Environment Variables:**
    Create a `.env` file. If `GROQ_API_KEY` is set, Groq will be used. Otherwise, falls back to local Ollama.

    **Option A: Use Groq (cloud)**
    ```bash
    GROQ_API_KEY=your_groq_api_key_here
    GROQ_MODEL=qwen/qwen3-32b
    ```

    **Option B: Use Ollama (local)**
    ```bash
    # No GROQ_API_KEY means Ollama will be used
    OLLAMA_MODEL=PetrosStav/gemma3-tools:4b
    OLLAMA_BASE_URL=http://localhost:11434
    ```

    Pull the Ollama model if using local:
    ```bash
    ollama pull PetrosStav/gemma3-tools:4b
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
- **Groq/Ollama**: LLM inference via Groq cloud (`qwen/qwen3-32b`) or local Ollama (`PetrosStav/gemma3-tools:4b`).
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
