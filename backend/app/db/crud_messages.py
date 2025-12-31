from sqlalchemy.orm import Session
from app.db.models import Conversation,Message

def create_conversation(db:Session,title:str|None = None):
    convo=Conversation(title=title)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo

def add_message(db:Session,conversation_id:int,role:str,content:str):
    msg=Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(db:Session,conversation_id:int,limit:int=10):
    return(
        db.query(Message)
        .filter(Message.conversation_id==conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )[::-1]