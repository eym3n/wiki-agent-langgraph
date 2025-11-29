from typing import List
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agent.state import AgentState
from src.agent.nodes.router import RouterNode
from src.agent.nodes.context import ContextNode
from src.agent.nodes.synthesize import SynthesizeNode
from src.agent.nodes.reply import ReplyNode
from src.agent.edges import should_continue, route_decision


def create_graph(tools: List[StructuredTool], checkpointer: BaseCheckpointSaver):
    # Initialize Nodes
    router_node = RouterNode()
    context_node = ContextNode(tools)
    synthesize_node = SynthesizeNode()
    reply_node = ReplyNode()
    tool_node = ToolNode(tools)

    # Build Graph
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("context", context_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("reply", reply_node)
    workflow.add_node("tools", tool_node)

    # Edges
    workflow.add_edge(START, "router")

    workflow.add_conditional_edges(
        "router", route_decision, {"context": "context", "reply": "reply"}
    )

    # Context loop
    workflow.add_conditional_edges(
        "context", should_continue, {"tools": "tools", "synthesize": "synthesize"}
    )
    workflow.add_edge("tools", "context")

    # End states
    workflow.add_edge("synthesize", END)
    workflow.add_edge("reply", END)

    return workflow.compile(checkpointer=checkpointer)
