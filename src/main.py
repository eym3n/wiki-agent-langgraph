from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
import os
import sys

from src.core.config import get_settings
from src.core.logging import setup_logging
from src.api.routers import chat
from src.services.agent_service import agent_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await agent_service.initialize()
    yield
    # Shutdown
    await agent_service.shutdown()


app = FastAPI(title="Wiki-Bot MCP Agent", lifespan=lifespan)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


def start():
    settings = get_settings()
    if not settings.google_api_key:
        print("Error: GOOGLE_API_KEY not found in environment.")
        sys.exit(1)

    uvicorn.run("src.main:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    start()
