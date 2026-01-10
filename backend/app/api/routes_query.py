from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation

from app.retrieval.multiquery import multiquery_search
from app.retrieval.rerank import rerank
from app.llm.answer_generator import generate_answer_with_history


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QueryRequest(BaseModel):
    query: str
    k: int = 5
    conversation_id: int | None = None


@router.post("/query")
async def query(req: QueryRequest, db: Session = Depends(get_db)):

    conversation = None

    # 🔹 If ID was provided, try to fetch it
    if req.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id)
            .first()
        )

    # 🔹 If conversation missing or invalid → create new one
    if conversation is None:
        conversation = crud_messages.create_conversation(db)

    conversation_id = conversation.id

    # 🟢 Save user message
    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=req.query,
    )

    # 🟢 Load last 10 messages for context
    history = crud_messages.get_recent_messages(
        db, conversation_id, limit=10
    )
    history_pairs = [(m.role, m.content) for m in history]

    # 🔍 Multi-query expand → retrieve → rerank
    candidates = multiquery_search(
        req.query,
        conversation_id=conversation_id,
        k=req.k * 4)
    docs = rerank(req.query, candidates, top_k=req.k)

    print("🔎 Retrieved docs count:", len(docs))
    print("🔎 Retrieved docs preview:", docs[:1])
    if not docs:
        answer = "I don't have enough information in my documents to answer that."
    else:
        answer = generate_answer_with_history(
            req.query, docs, history_pairs
        )


    # 🤖 Generate answer with conversation history
    answer = generate_answer_with_history(
        req.query, docs, history_pairs
    )

    # 🟢 Save assistant reply
    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "contexts": docs,
    }
