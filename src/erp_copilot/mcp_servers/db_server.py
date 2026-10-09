"""MCP server exposing read-only database access to the ERP agent (stdio transport)."""

import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from erp_copilot import db

mcp = MCPServer("erp-db")


@mcp.tool()
def describe_table(table: str) -> str:
    """Return the columns and types of an allowed table. Use when the schema summary is not enough."""
    try:
        return json.dumps(db.describe_table(table))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def run_query(sql: str) -> str:
    """Run one read-only SQLite SELECT query on the ERP order tables. Use for any question about
    order data: lookups, counts, totals, filters, comparisons. Returns columns and up to 100 rows."""
    try:
        return json.dumps(db.run_select(sql))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


if __name__ == "__main__":
    db.init_db()
    mcp.run()
