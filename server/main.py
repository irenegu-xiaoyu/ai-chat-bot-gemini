from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
from google import genai
from gemini_api_config import GEMINI_API_KEY

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

app = FastAPI(title="Mock AI Agent")

# Allow requests from Next dev server
# During local development allow the common dev origins. In production
# you should restrict this to your deployed frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=req.message)
        return ChatResponse(reply=response.text)
    except Exception as e:
        # On error calling the external API, return a 502 with details
        raise HTTPException(status_code=502, detail=f"upstream error: {e}")
