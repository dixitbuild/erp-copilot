from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from groq import APIError
from pydantic import BaseModel, Field

from erp_copilot.agents.erp import build_erp_agent
from erp_copilot.agents.guard import check_query
from erp_copilot.config import pinecone_configured
from erp_copilot.tools.client import McpToolbox
from erp_copilot.api.routers.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    modules = ["erp_copilot.tools.db_server"]
    if pinecone_configured():  # knowledge search is optional: skipped until PINECONE_API_KEY is set
        modules.append("erp_copilot.tools.knowledge_server")
    toolbox = McpToolbox(modules)
    await toolbox.start()
    app.state.toolbox = toolbox
    app.state.erp_agent = build_erp_agent()
    yield
    await toolbox.stop()


app = FastAPI(title="ERP Copilot", lifespan=lifespan)
app.include_router(orders_router)

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
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    try:
        verdict = await check_query(request.message)
        if verdict.injection_detected:
            return ChatResponse(agent="guard", blocked=True, reply=INJECTION_MESSAGE)
        if not verdict.is_relevant:
            return ChatResponse(agent="guard", blocked=True, reply=IRRELEVANT_MESSAGE)
        erp_agent = http_request.app.state.erp_agent
        reply = await erp_agent.run_with_tools(request.message, http_request.app.state.toolbox)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"Groq API error: {exc}") from exc
    return ChatResponse(agent=erp_agent.name, blocked=False, reply=reply)
