from fastapi import FastAPI, HTTPException
from groq import APIError
from pydantic import BaseModel, Field

from erp_copilot.agents.erp import erp_agent
from erp_copilot.agents.guard import check_query

app = FastAPI(title="ERP Copilot")

IRRELEVANT_MESSAGE = (
    "Please ask a relevant question about sales orders, purchase orders or work orders."
)
INJECTION_MESSAGE = "Your message looks like an attempt to manipulate the assistant, so it was blocked."


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    agent: str
    blocked: bool
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        verdict = await check_query(request.message)
        if verdict.injection_detected:
            return ChatResponse(agent="guard", blocked=True, reply=INJECTION_MESSAGE)
        if not verdict.is_relevant:
            return ChatResponse(agent="guard", blocked=True, reply=IRRELEVANT_MESSAGE)
        reply = await erp_agent.run(request.message)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Groq API error: {exc}") from exc
    return ChatResponse(agent=erp_agent.name, blocked=False, reply=reply)
