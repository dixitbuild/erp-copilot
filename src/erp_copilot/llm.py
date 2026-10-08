import json
from collections.abc import Awaitable, Callable
from functools import lru_cache

from groq import AsyncGroq

from erp_copilot.config import get_settings


@lru_cache
def get_groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=get_settings().groq_api_key)


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    settings = get_settings()
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    response = await get_groq_client().chat.completions.create(
        model=model or settings.groq_model,
        messages=messages,
        temperature=settings.groq_temperature if temperature is None else temperature,
        **kwargs,
    )
    return response.choices[0].message.content or ""


async def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    call_tool: Callable[[str, dict], Awaitable[str]],
    model: str | None = None,
    temperature: float | None = None,
    max_steps: int = 5,
) -> str:
    """Let the model call tools until it produces a final answer (at most max_steps rounds)."""
    settings = get_settings()
    messages = list(messages)
    for _ in range(max_steps):
        response = await get_groq_client().chat.completions.create(
            model=model or settings.groq_model,
            messages=messages,
            tools=tools,
            temperature=settings.groq_temperature if temperature is None else temperature,
        )
        message = response.choices[0].message
        print('----------message.tool_calls----------------', message.tool_calls)
        print('----------message.content----------------', message.content)
        if not message.tool_calls:
            return message.content or ""
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {"name": c.function.name, "arguments": c.function.arguments},
                    }
                    for c in message.tool_calls
                ],
            }
        )
        print('----------messages----------------', messages)
        for call in message.tool_calls:
            try:
                result = await call_tool(call.function.name, json.loads(call.function.arguments or "{}"))
            except Exception as exc:  # report tool failures to the model instead of crashing
                result = f"Error: {exc}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Sorry, I could not finish answering within the allowed number of steps."
