from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Optional, List
from langgraph.graph.message import add_messages


def replace_list(old_list: List[str], new_list: List[str]) -> List[str]:
    # When new_list is provided in an update, it replaces the old list.
    # If we wanted merge logic, we'd implement it here.
    # But our node logic (context.py) already merges with existing state.
    # So we just need to ensure the return value from the node *becomes* the new state.
    # Standard behavior for Pydantic models in LangGraph is overwrite.
    return new_list


class AgentState(BaseModel):
    messages: Annotated[list[Any], add_messages]
    # We need to ensure that updates to this field overwrite the previous value.
    # LangGraph's default for Pydantic fields is overwrite, but let's be explicit or check node logic.
    # The issue might be that state.referenced_article_urls is empty when read in SynthesizeNode.
    # This happens if ContextNode's update didn't persist or wasn't picked up.

    # Actually, if we look at ContextNode, it returns:
    # {"messages": [response], "referenced_article_urls": merged_urls}

    # If LangGraph treats this as an update, it should work.
    # One possibility: Pydantic model validation or default factory resetting it?

    referenced_article_urls: Annotated[List[str], replace_list] = Field(
        default_factory=list
    )
    next_step: Optional[Literal["context", "reply"]] = None
