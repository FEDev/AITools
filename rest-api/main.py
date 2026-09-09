"""
rest-api/main.py — plain HTTP REST wrapper around ai_trader_tools.

Works from ANY language/runtime (Next.js API routes, Node, Python, curl, Postman,
OpenAI "custom GPT actions", any HTTP-capable agent framework) — no MCP or Python
import required on the caller's side.

Run:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8080

Endpoints:
    GET  /tools                  -> full tool manifest (same content as tools-manifest/*.json)
    POST /tools/{tool_name}      -> body = JSON kwargs for that tool; returns the tool's result
    GET  /health                 -> liveness check
"""
import json
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools-manifest"))

from ai_trader_tools.registry import TOOL_REGISTRY  # noqa: E402
from tool_specs import TOOLS  # noqa: E402

app = FastAPI(
    title="AI Trader Tools API",
    description="Open-source REST API for AI/LLM trading agents — market data, TA, sentiment, execution, risk.",
    version="0.1.0",
)

# Open by default so browser-based apps (e.g. a Next.js frontend) can call it directly.
# Lock this down (specific origins) before exposing publicly with live trading keys.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ToolCallResponse(BaseModel):
    tool: str
    result: dict | list | None = None
    error: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "tool_count": len(TOOL_REGISTRY)}


@app.get("/tools")
def list_tools():
    return {"tools": TOOLS}


@app.post("/tools/{tool_name}", response_model=ToolCallResponse)
def call_tool(tool_name: str, payload: dict = None):
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown tool '{tool_name}'. See GET /tools.")
    kwargs = payload or {}
    try:
        result = TOOL_REGISTRY[tool_name](**kwargs)
        return {"tool": tool_name, "result": result}
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Bad parameters for '{tool_name}': {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
