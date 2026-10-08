from dataclasses import dataclass

from erp_copilot.llm import chat_completion, chat_with_tools
from erp_copilot.mcp_client import McpToolbox


@dataclass
class Agent:
    """A single LLM-backed agent. The orchestrator will route work between these."""

    name: str
    system_prompt: str
    model: str | None = None
    temperature: float | None = None
    json_mode: bool = False

    async def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        return await chat_completion(
            messages,
            model=self.model,
            temperature=self.temperature,
            json_mode=self.json_mode,
        )

    async def run_with_tools(self, user_input: str, toolbox: McpToolbox) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        return await chat_with_tools(
            messages,
            tools=toolbox.tools,
            call_tool=toolbox.call,
            model=self.model,
            temperature=self.temperature,
        )
