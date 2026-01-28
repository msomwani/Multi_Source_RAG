from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        index=True,
    )
    role = Column(String)
    content = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    meta = Column(JSON, nullable=True)

    conversation = relationship("Conversation")
