from sqlalchemy import Column,String,Integer,DateTime,Text,ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .session import Base
from sqlalchemy import JSON

class Document(Base):
    __tablename__="documents"

    id=Column(Integer,primary_key=True)
    source=Column(String)
    name=Column(String)
    doc_metadata=Column(JSONB)
    created_at=Column(DateTime(timezone=True),server_default=func.now())


class Conversation(Base):
    __tablename__="conversations"

    id=Column(Integer,primary_key=True)
    title=Column(String)
    created_at=Column(DateTime(timezone=True),server_default=func.now())


class Message(Base):
    __tablename__="messages"

    id=Column(Integer,primary_key=True)
    conversation_id=Column(Integer,ForeignKey("conversations.id"))
    role=Column(String)
    content=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    meta=Column(JSON,nullable=True)