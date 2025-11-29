import sys
import json
import logging
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from src.mcp.mcp_client_utils import mcp_server_context, load_mcp_tools
from src.agent.graph import create_graph

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        load_dotenv()
        self.agent: Optional[CompiledStateGraph] = None
        self.checkpointer: Optional[AsyncSqliteSaver] = None
        self._checkpointer_cm = None
        self._mcp_cm = None
        self._mcp_session = None

    async def initialize(self):
        logger.info("Initializing AgentService...")
        self._checkpointer_cm = AsyncSqliteSaver.from_conn_string("checkpoints.db")
        self.checkpointer = await self._checkpointer_cm.__aenter__()

        cmd = sys.executable
        args = ["-m", "wikipedia_mcp"]

        logger.info("Starting MCP Server...")
        self._mcp_cm = mcp_server_context(cmd, args)
        self._mcp_session = await self._mcp_cm.__aenter__()

        logger.info("Connected to MCP Server. Loading tools...")
        tools = await load_mcp_tools(self._mcp_session)
        logger.info(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

        self.agent = create_graph(tools, self.checkpointer)
        logger.info("AgentService initialized successfully.")

    async def shutdown(self):
        logger.info("Shutting down AgentService...")
        if self._mcp_cm:
            await self._mcp_cm.__aexit__(None, None, None)
            self._mcp_cm = None
            self._mcp_session = None
        if self._checkpointer_cm:
            await self._checkpointer_cm.__aexit__(None, None, None)
            self._checkpointer_cm = None
            self.checkpointer = None
        logger.info("AgentService shutdown complete.")

    async def chat_stream(
        self, message: str, thread_id: str
    ) -> AsyncGenerator[str, None]:
        if not self.agent:
            logger.error("Agent not initialized")
            raise RuntimeError("Agent not initialized")

        logger.info(f"Starting chat stream for thread_id: {thread_id}")
        config = {"configurable": {"thread_id": thread_id}}
        input_message = HumanMessage(content=message)
        # Reset references for new turn but keep messages
        initial_state = {
            "messages": [input_message],
            "referenced_article_urls": [],
        }
        latest_references: list[str] = []

        try:
            async for event in self.agent.astream(
                initial_state, config=config, stream_mode="updates"
            ):
                logger.debug(f"Received event: {event}")
                for node, values in event.items():
                    if "referenced_article_urls" in values:
                        latest_references = values["referenced_article_urls"] or []

                    if node in ["synthesize", "reply"] and values.get("messages"):
                        msg = values["messages"][-1]
                        content = getattr(msg, "content", None)
                        if content:
                            payload = {"content": content}
                            if latest_references:
                                payload["references"] = latest_references
                            yield f"data: {json.dumps(payload)}\n\n"
                    elif node == "tools" and values.get("messages"):
                        for msg in values["messages"]:
                            payload = {"tool": msg.name}
                            if latest_references:
                                payload["references"] = latest_references
                            yield f"data: {json.dumps(payload)}\n\n"
                    elif node == "router":
                        next_step = values.get("next_step")
                        if next_step:
                            payload = {"router": next_step}
                            if latest_references:
                                payload["references"] = latest_references
                            yield f"data: {json.dumps(payload)}\n\n"

            if latest_references:
                yield f"data: {json.dumps({'references': latest_references})}\n\n"

            yield "data: [DONE]\n\n"
            logger.info(f"Chat stream completed for thread_id: {thread_id}")
        except Exception as e:
            logger.error(f"Error in chat stream: {str(e)}", exc_info=True)
            yield f"data: [ERROR] {str(e)}\n\n"


# Global instance
agent_service = AgentService()


async def get_agent_service() -> AgentService:
    return agent_service
