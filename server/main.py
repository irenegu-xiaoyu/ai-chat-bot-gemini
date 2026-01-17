from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
from google import genai
import json
from pathlib import Path


# Load Gemini config from JSON file (project root) with environment fallback.
CONFIG_PATH = Path(__file__).resolve().parent.parent / "gemini_api_config.json"


def load_gemini_config(path: Path) -> dict:
    cfg = {}
    try:
        if path.exists() and path.stat().st_size > 0:
            with path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
    except Exception as e:
        # If JSON is malformed or unreadable, raise so the server fails fast.
        raise RuntimeError(f"Failed to load Gemini config from {path}: {e}")

    api_key = cfg.get("api_key")
    model = cfg.get("model") or "gemini-3-flash-preview"

    return {"api_key": api_key, "model": model}


config = load_gemini_config(CONFIG_PATH)


app = FastAPI(title="Mock AI Agent")

# Allow requests from Next dev server
# During local development allow the common dev origins. In production
# you should restrict this to your deployed frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key = config["api_key"])

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        response = client.models.generate_content(model=config["model"], contents=req.message)
        return ChatResponse(reply=response.text)
    except Exception as e:
        # On error calling the external API, return a 502 with details
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")
