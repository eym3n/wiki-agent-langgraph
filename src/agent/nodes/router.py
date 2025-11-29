from datetime import datetime
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.agent.state import AgentState
from src.agent.prompts.route_prompt import get_route_prompt
from src.core.config import get_settings


class RouteResponse(BaseModel):
    step: Literal["context", "reply"] = Field(
        description="The next step in the routing process"
    )


def _get_router_llm():
    """Use a separate model for routing that's better at following instructions."""
    settings = get_settings()
    if settings.use_groq:
        from langchain_groq import ChatGroq

        # Use llama for routing - it follows structured output better than qwen3
        return ChatGroq(
            model=settings.groq_router_model,
            api_key=settings.groq_api_key,
            temperature=0,
        )
    else:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )


class RouterNode:
    def __init__(self, model_name: str = None):
        self.llm = _get_router_llm()
        self.structured_llm = self.llm.with_structured_output(RouteResponse)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYSTEM_PROMPT = SystemMessage(content=get_route_prompt(current_datetime))
        messages = [SYSTEM_PROMPT] + state.messages
        response = self.structured_llm.invoke(messages)
        return {"next_step": response.step, "referenced_article_urls": []}
