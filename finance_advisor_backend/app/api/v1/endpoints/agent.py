"""
app/api/v1/endpoints/agent.py
-----------------------------
FastAPI endpoint for interacting with the AI Agent Tori.
Supports streaming or simple message-response cycles.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.agent.tori_agent import ask_tori
from app.agent.memory import save_message, get_chat_history
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: int
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_tori(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Sends a message to Tori and returns the AI-generated response.
    Persists the conversation in the database.
    """
    # 1. Fetch recent history
    history_objs = await get_chat_history(db, request.user_id)
    # Convert to LangChain format (simple tuple list for now)
    history = []
    for msg in history_objs:
        history.append((msg.role, msg.content))

    # 2. Get AI response
    try:
        # Save user message first
        await save_message(db, request.user_id, "user", request.message)
        
        reply = await ask_tori(request.message, request.user_id, history)
        
        # Save assistant message
        await save_message(db, request.user_id, "assistant", reply)
        
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@router.get("/history/{user_id}")
async def fetch_history(user_id: int, db: AsyncSession = Depends(get_db)):
    """Returns the chat history for a specific user."""
    history = await get_chat_history(db, user_id)
    return history
