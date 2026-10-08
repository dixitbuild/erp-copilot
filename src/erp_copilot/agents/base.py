from dataclasses import dataclass

from erp_copilot.llm import chat_completion


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
