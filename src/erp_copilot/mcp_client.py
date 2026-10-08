import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from erp_copilot.db import DEFAULT_ALLOWED_TABLES


class McpToolbox:
    """Starts an MCP server as a subprocess and exposes its tools in Groq's function-calling format."""

    def __init__(self, module: str, allowed_tables: tuple[str, ...] = DEFAULT_ALLOWED_TABLES):
        self._params = StdioServerParameters(
            command=sys.executable,
            args=["-m", module],
            env={"ERP_ALLOWED_TABLES": ",".join(allowed_tables)},
        )
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []

    async def start(self) -> None:
        read, write = await self._stack.enter_async_context(stdio_client(self._params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        listed = await self._session.list_tools()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.input_schema,
                },
            }
            for t in listed.tools
        ]

    async def stop(self) -> None:
        await self._stack.aclose()

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        assert self._session is not None, "McpToolbox.start() was not called"
        result = await self._session.call_tool(name, arguments)
        text = "\n".join(getattr(c, "text", "") for c in result.content)
        return f"Error: {text}" if result.is_error else text
