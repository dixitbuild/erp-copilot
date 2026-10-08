from functools import lru_cache

from groq import AsyncGroq

from erp_copilot.config import get_settings


@lru_cache
def get_groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=get_settings().groq_api_key)


async def chat_completion(messages: list[dict[str, str]], model: str | None = None) -> str:
    settings = get_settings()
    response = await get_groq_client().chat.completions.create(
        model=model or settings.groq_model,
        messages=messages,
        temperature=settings.groq_temperature,
    )
    return response.choices[0].message.content or ""
