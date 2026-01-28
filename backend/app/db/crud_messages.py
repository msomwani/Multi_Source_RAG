from sqlalchemy.orm import Session
from app.db.models import Conversation, Message


def create_conversation(
    db: Session,
    title: str | None = None,
):
    convo = Conversation(title=title)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    meta: dict | None = None,
):
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        meta=meta,
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(
    db: Session,
    conversation_id: int,
    limit: int = 10,
):
    """
    Returns messages in chronological order (oldest → newest),
    limited to the most recent `limit`.
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    return list(reversed(messages))
