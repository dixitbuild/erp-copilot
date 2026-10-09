"""MCP server that searches the ERP knowledge docs stored in Pinecone (stdio transport)."""

import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from erp_copilot.vector import store as vector_store
from erp_copilot.config import pinecone_configured

mcp = MCPServer("erp-knowledge")


@mcp.tool()
def search_knowledge(query: str, top_k: int = 3) -> str:
    """Search ERP policy and process documents (order lifecycles, approval rules, cancellation
    and escalation policies, glossary). Use for how/why/what-is-the-rule questions. Do NOT use it
    for order data or numbers. Returns the most relevant passages with their source."""
    if not pinecone_configured():
        raise ToolError("Knowledge search is not configured: PINECONE_API_KEY is missing.")
    try:
        return json.dumps(vector_store.search(query, top_k=max(1, min(top_k, 5))))
    except Exception as exc:
        raise ToolError(f"Knowledge search failed: {exc}") from exc


if __name__ == "__main__":
    mcp.run()
