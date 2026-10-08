from dataclasses import dataclass

from erp_copilot.llm import chat_completion


@dataclass
class Agent:
    """A single LLM-backed agent. The orchestrator will route work between these."""

    name: str
    system_prompt: str
    model: str | None = None

    async def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        return await chat_completion(messages, model=self.model)


general_agent = Agent(
    name="general",
    system_prompt="You are ERP Copilot, a helpful assistant for ERP-related questions.",
)
