from datetime import datetime
from typing import Literal
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import AgentState
from src.agent.prompts.route_prompt import get_route_prompt


class RouteResponse(BaseModel):
    step: Literal["context", "reply"] = Field(
        description="The next step in the routing process"
    )


class RouterNode:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.structured_llm = self.llm.with_structured_output(RouteResponse)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYSTEM_PROMPT = SystemMessage(content=get_route_prompt(current_datetime))
        messages = [SYSTEM_PROMPT] + state.messages
        response = self.structured_llm.invoke(messages)
        return {"next_step": response.step, "referenced_article_urls": []}
