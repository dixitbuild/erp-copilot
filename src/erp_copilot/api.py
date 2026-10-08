from fastapi import FastAPI, HTTPException
from groq import APIError
from pydantic import BaseModel, Field

from erp_copilot.agents.base import general_agent

app = FastAPI(title="ERP Copilot")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    agent: str
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await general_agent.run(request.message)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Groq API error: {exc}") from exc
    return ChatResponse(agent=general_agent.name, reply=reply)
