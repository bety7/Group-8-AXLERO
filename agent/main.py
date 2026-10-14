"""FastAPI service: streams agent events to the Next.js UI over Server-Sent Events."""
import asyncio
import json
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent import get_context, run_agent
from config import LLM_PROVIDER, WEB_ORIGIN
from cube_client import CubeClient, CubeError

app = FastAPI(title="MetricMind Agent")
app.add_middleware(CORSMiddleware, allow_origins=[WEB_ORIGIN], allow_methods=["*"], allow_headers=["*"])


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Msg] = Field(min_length=1, max_length=20)


@app.get("/health")
async def health():
    try:
        await asyncio.to_thread(CubeClient().meta)
        layer = "ok"
    except CubeError:
        layer = "down"
    return {"agent": "ok", "semantic_layer": layer, "llm_provider": LLM_PROVIDER}


@app.get("/metrics")
async def metrics():
    try:
        catalog, _ = await asyncio.to_thread(get_context, CubeClient())
        return catalog.public()
    except CubeError:
        return []


@app.post("/chat")
async def chat(req: ChatRequest):
    history = [m.model_dump() for m in req.messages]

    async def stream():
        try:
            async for event in run_agent(history):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
