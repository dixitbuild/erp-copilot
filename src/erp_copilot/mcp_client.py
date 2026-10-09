import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from erp_copilot.db import DEFAULT_ALLOWED_TABLES


class McpToolbox:
    """Starts one or more MCP servers as subprocesses and exposes all their tools in Groq's
    function-calling format. Calls are routed to the server that owns the tool."""

    def __init__(self, modules: list[str], allowed_tables: tuple[str, ...] = DEFAULT_ALLOWED_TABLES):
        self._params = [
            StdioServerParameters(
                command=sys.executable,
                args=["-m", module],
                env={"ERP_ALLOWED_TABLES": ",".join(allowed_tables)},
            )
            for module in modules
        ]
        self._stack = AsyncExitStack()
        self._owner: dict[str, ClientSession] = {}
        self.tools: list[dict[str, Any]] = []

    async def start(self) -> None:
        for params in self._params:
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            for tool in (await session.list_tools()).tools:
                if tool.name in self._owner:
                    raise ValueError(f"Duplicate MCP tool name: {tool.name}")
                self._owner[tool.name] = session
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )

    async def stop(self) -> None:
        await self._stack.aclose()

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        session = self._owner.get(name)
        if session is None:
            return f"Error: unknown tool '{name}'"
        result = await session.call_tool(name, arguments)
        text = "\n".join(getattr(c, "text", "") for c in result.content)
        return f"Error: {text}" if result.is_error else text
