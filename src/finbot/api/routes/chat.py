"""Chat advisor endpoints."""
from fastapi import APIRouter, HTTPException

from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import ChatMessageOut, ChatRequest, ChatSessionOut
from finbot.llm.analyst import ask_advisor
from finbot.llm.memory import add_message, create_session, get_messages, list_sessions
from finbot.llm.prompts import BOGLEHEAD_SYSTEM_PROMPT, MUNI_BONDS_SYSTEM_PROMPT, TAX_OPTIMIZER_SYSTEM_PROMPT
from finbot.models.chat_session import ChatMessage, ChatSession

router = APIRouter(prefix="/api/chat", tags=["chat"])

_PROMPTS = {
    "boglehead": BOGLEHEAD_SYSTEM_PROMPT,
    "tax": TAX_OPTIMIZER_SYSTEM_PROMPT,
    "muni": MUNI_BONDS_SYSTEM_PROMPT,
}


@router.get("/sessions", response_model=list[ChatSessionOut])
def get_sessions(db: DbSession, _user: CurrentUser, advisor_type: str | None = None):
    sessions = list_sessions(db, advisor_type)
    result = []
    for s in sessions:
        count = db.query(ChatMessage).filter_by(session_id=s.id).count()
        result.append(ChatSessionOut(
            id=s.id, advisor_type=s.advisor_type, title=s.title,
            created_at=str(s.created_at)[:19], message_count=count,
        ))
    return result


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_session_messages(session_id: int, db: DbSession, _user: CurrentUser):
    msgs = get_messages(db, session_id)
    return [ChatMessageOut(id=i, role=m["role"], content=m["content"], created_at="") for i, m in enumerate(msgs)]


@router.post("/message")
def send_message(body: ChatRequest, db: DbSession, _user: CurrentUser):
    prompt = _PROMPTS.get(body.advisor_type, BOGLEHEAD_SYSTEM_PROMPT)

    if body.session_id:
        session_id = body.session_id
    else:
        cs = create_session(db, body.advisor_type, body.message[:50])
        db.commit()
        session_id = cs.id

    add_message(db, session_id, "user", body.message)
    db.commit()

    response = ask_advisor(db, prompt, body.message)

    add_message(db, session_id, "assistant", response)
    db.commit()

    return {"session_id": session_id, "response": response}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: DbSession, _user: CurrentUser):
    s = db.query(ChatSession).get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    db.query(ChatMessage).filter_by(session_id=session_id).delete()
    db.delete(s)
    db.commit()
    return {"status": "deleted"}
