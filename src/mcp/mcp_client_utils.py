import sys
import shutil
import asyncio
from typing import List, Any, Dict, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import StructuredTool
from pydantic import create_model


class MCPClientManager:
    def __init__(
        self, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ):
        self.params = StdioServerParameters(command=command, args=args, env=env)
        self.session: Optional[ClientSession] = None
        self._exit_stack = None

    async def __aenter__(self):
        self._exit_stack = await stdio_client(self.params).__aenter__()
        self.read, self.write = self._exit_stack
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self._exit_stack:
            pass

        pass

    async def get_tools(self) -> List[StructuredTool]:
        if not self.session:
            raise RuntimeError("Session not initialized")

        mcp_tools = await self.session.list_tools()
        langchain_tools = []

        for tool in mcp_tools.tools:

            async def _tool_wrapper(**kwargs):
                return await self.session.call_tool(tool.name, arguments=kwargs)

            fields = {}
            if tool.inputSchema and "properties" in tool.inputSchema:
                for name, prop in tool.inputSchema["properties"].items():
                    fields[name] = (Any, ...)

            InputModel = create_model(f"{tool.name}_input", **fields)

            langchain_tool = StructuredTool.from_function(
                func=None,
                coroutine=_tool_wrapper,
                name=tool.name,
                description=tool.description or "",
                args_schema=InputModel,
            )
            langchain_tools.append(langchain_tool)

        return langchain_tools


@asynccontextmanager
async def mcp_server_context(command: str, args: List[str]):
    async with stdio_client(
        StdioServerParameters(command=command, args=args)
    ) as streams:
        read, write = streams
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def load_mcp_tools(session: ClientSession) -> List[StructuredTool]:
    result = await session.list_tools()
    langchain_tools = []

    for tool in result.tools:

        async def _wrapper(tool_name=tool.name, **kwargs):
            res = await session.call_tool(tool_name, arguments=kwargs)
            return [c.text for c in res.content if c.type == "text"]

        schema = tool.inputSchema or {}
        props = schema.get("properties", {})
        required = schema.get("required", [])

        fields = {}
        for field_name, field_info in props.items():
            field_type = Any
            t = field_info.get("type")
            if t == "string":
                field_type = str
            elif t == "integer":
                field_type = int
            elif t == "boolean":
                field_type = bool
            elif t == "number":
                field_type = float

            default = ... if field_name in required else None
            fields[field_name] = (field_type, default)

        if not fields:
            InputModel = create_model(f"{tool.name}Input")
        else:
            InputModel = create_model(f"{tool.name}Input", **fields)

        lc_tool = StructuredTool.from_function(
            func=None,
            coroutine=_wrapper,
            name=tool.name,
            description=tool.description,
            args_schema=InputModel,
        )
        langchain_tools.append(lc_tool)

    return langchain_tools
