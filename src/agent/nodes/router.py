from datetime import datetime
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from src.agent.state import AgentState
from src.agent.prompts.route_prompt import get_route_prompt
from src.core.config import get_settings


class RouteResponse(BaseModel):
    step: Literal["context", "reply"] = Field(
        description="The next step in the routing process"
    )


class RouterNode:
    def __init__(self, model_name: str = None):
        settings = get_settings()
        model = model_name or settings.ollama_model
        self.llm = ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0
        )
        self.structured_llm = self.llm.with_structured_output(RouteResponse)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYSTEM_PROMPT = SystemMessage(content=get_route_prompt(current_datetime))
        messages = [SYSTEM_PROMPT] + state.messages
        response = self.structured_llm.invoke(messages)
        return {"next_step": response.step, "referenced_article_urls": []}
