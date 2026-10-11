"""Shared pieces for the LangChain / LangGraph experiments.

Reuses the main project's settings, prompts and MCP servers (src/erp_copilot) so the only thing
that differs between the three versions is the orchestration.
"""

from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from erp_copilot.agents.erp import build_erp_agent
from erp_copilot.config import get_settings, pinecone_configured
from erp_copilot.tools.client import McpToolbox

GROQ_OPENAI_URL = "https://api.groq.com/openai/v1"  # langchain-groq needs groq<1, so use Groq's OpenAI-compatible API


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        base_url=GROQ_OPENAI_URL,
        temperature=0,
    )

# just taking system prompt from erp agent for now.
def erp_system_prompt() -> str:
    return build_erp_agent().system_prompt


async def start_toolbox() -> McpToolbox:
    modules = ["erp_copilot.tools.db_server"]
    if pinecone_configured():
        modules.append("erp_copilot.tools.knowledge_server")
    toolbox = McpToolbox(modules)
    await toolbox.start()
    return toolbox


def to_langchain_tools(toolbox: McpToolbox) -> list[StructuredTool]:
    """Wrap the MCP tools as LangChain tools (langchain-mcp-adapters does not support mcp 2.x yet)."""

    def make(spec: dict) -> StructuredTool:
        fn = spec["function"]
        name = fn["name"]

        async def call(**kwargs) -> str:
            return await toolbox.call(name, kwargs)

        return StructuredTool.from_function(
            coroutine=call,
            name=name,
            description=fn["description"],
            args_schema=fn["parameters"],
        )

    return [make(spec) for spec in toolbox.tools]
