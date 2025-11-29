from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from src.api.schemas import ChatRequest
from src.services.agent_service import get_agent_service, AgentService

router = APIRouter()


@router.post("/chat")
async def chat(
    request: ChatRequest, service: AgentService = Depends(get_agent_service)
):
    if not service.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return StreamingResponse(
        service.chat_stream(request.message, request.thread_id),
        media_type="text/event-stream",
    )
