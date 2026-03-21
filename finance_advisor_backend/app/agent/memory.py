"""
app/agent/memory.py
-------------------
DB-backed conversation history for the Tori AI Agent.
Uses SQLAlchemy async to store and retrieve chat messages.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

class ChatMessage(Base):
    """Stores individual messages in a conversation."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", backref="chat_history")

async def save_message(db, user_id: int, role: str, content: str):
    msg = ChatMessage(user_id=user_id, role=role, content=content)
    db.add(msg)
    await db.commit()

async def get_chat_history(db, user_id: int, limit: int = 10):
    from sqlalchemy import select
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    # Convert to LangChain format if needed elsewhere, but for now return flat list
    return messages[::-1]  # Return in chronological order
