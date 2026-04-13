"""Conversation persistence and retrieval."""
from __future__ import annotations

from sqlalchemy.orm import Session

from finbot.models.chat_session import ChatMessage, ChatSession


def create_session(db: Session, advisor_type: str, title: str | None = None) -> ChatSession:
    chat_session = ChatSession(advisor_type=advisor_type, title=title)
    db.add(chat_session)
    db.flush()
    return chat_session


def add_message(db: Session, session_id: int, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.flush()
    return msg


def get_messages(db: Session, session_id: int) -> list[dict[str, str]]:
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def list_sessions(db: Session, advisor_type: str | None = None) -> list[ChatSession]:
    q = db.query(ChatSession)
    if advisor_type:
        q = q.filter_by(advisor_type=advisor_type)
    return q.order_by(ChatSession.updated_at.desc()).all()
