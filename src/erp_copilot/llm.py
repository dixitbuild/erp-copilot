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
