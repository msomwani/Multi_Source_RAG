from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation, Message
from datetime import datetime

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- SCHEMAS ----------
from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- ROUTES ----------

@router.post("", response_model=ConversationOut)
def create_conversation(db: Session = Depends(get_db)):
    convo = crud_messages.create_conversation(db)
    return convo


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()


@router.get("/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):

    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return {
        "conversation": convo,
        "messages": messages
    }


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):

    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # delete messages
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()

    # delete conversation
    db.delete(convo)
    db.commit()

    return {"status": "deleted", "conversation_id": conversation_id}
