
from typing import List
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import AgentState

class AgentNode:
    def __init__(self, tools: List[StructuredTool], model_name: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.llm_with_tools = self.llm.bind_tools(tools)

    def __call__(self, state: AgentState):
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

