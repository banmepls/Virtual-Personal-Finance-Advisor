"""
app/api/v1/endpoints/agent.py
-----------------------------
FastAPI endpoint for interacting with the AI Agent Tori.
Supports streaming or simple message-response cycles.
"""
from fastapi import APIRouter, Depends
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
    # Convert to LangChain format ("human" and "ai")
    history = []
    for msg in history_objs:
        role = "human" if msg.role == "user" else "ai"
        history.append((role, msg.content))

    # 2. Get AI response
    await save_message(db, request.user_id, "user", request.message)
    try:
        reply = await ask_tori(request.message, request.user_id, history)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Tori unavailable: {e}")
        reply = (
            "I'm temporarily unavailable because I can't reach the AI service right now. "
            "Please check your internet connection and try again. "
            "In the meantime, you can still view your transactions, budgets, and spending summary in the dashboard."
        )
    await save_message(db, request.user_id, "assistant", reply)
    return ChatResponse(response=reply)

@router.get("/history/{user_id}")
async def fetch_history(user_id: int, db: AsyncSession = Depends(get_db)):
    """Returns the chat history for a specific user."""
    history = await get_chat_history(db, user_id)
    return history
