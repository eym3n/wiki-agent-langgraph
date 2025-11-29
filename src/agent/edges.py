from typing import Literal
from langgraph.graph import END
from src.agent.state import AgentState


def should_continue(state: AgentState) -> Literal["tools", "synthesize"]:
    messages = state.messages
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "synthesize"


def route_decision(state: AgentState) -> Literal["context", "reply"]:
    if state.next_step == "context":
        return "context"
    return "reply"
