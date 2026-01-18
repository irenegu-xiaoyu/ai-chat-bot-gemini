from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
from google import genai
import json
from pathlib import Path
import time


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

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str


client = genai.Client(api_key = config["api_key"])

# In-memory store for chat sessions with metadata for cleanup.
# Format: { session_id: {"chat": ChatSession, "last_active": timestamp} }
chat_sessions = {}
SESSION_TIMEOUT = 1800  # 30 minutes in seconds

@app.on_event("startup")
async def startup_event():
    """Start the background session cleaner."""
    asyncio.create_task(clean_expired_sessions())


async def clean_expired_sessions():
    """Background task that removes inactive sessions every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        now = time.time()
        expired_ids = [
            sid for sid, data in chat_sessions.items()
            if now - data["last_active"] > SESSION_TIMEOUT
        ]
        for sid in expired_ids:
            try:
                # We can't easily 'close' a chat session object in the SDK,
                # but removing it from the dict allows it to be garbage collected.
                del chat_sessions[sid]
            except KeyError:
                pass
        if expired_ids:
            print(f"Cleaned up {len(expired_ids)} expired sessions.")


@app.on_event("shutdown")
async def _shutdown_client_aio():
    """Close the async client on shutdown to release resources."""
    try:
        await client.aio.aclose()
    except Exception:
        pass


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Async endpoint that streams Gemini chunks to the client.
    
    Uses `client.aio.chats` to maintain multi-turn conversation state asynchronously.
    """
    if not req.message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id = req.session_id or "default"
    
    # Get or create a chat session for this ID
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "chat": client.aio.chats.create(model=config["model"]),
            "last_active": time.time()
        }
    else:
        # Update last active time
        chat_sessions[session_id]["last_active"] = time.time()
    
    chat = chat_sessions[session_id]["chat"]

    async def stream_reply():
        try:
            # Send message and iterate over the async response stream
            async for chunk in await chat.send_message_stream(req.message):
                text = chunk.text
                if text is None:
                    continue
                yield text.encode("utf-8")
        except Exception as e:
            try:
                err_msg = f"\n[ERROR] upstream error: {e}\n"
                yield err_msg.encode("utf-8")
            except Exception:
                pass

    return StreamingResponse(stream_reply(), media_type="text/plain; charset=utf-8")
