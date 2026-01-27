from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation

from app.retrieval.hybrid import hybrid_retrieve
from app.llm.answer_generator import (
    generate_answer_with_history,
    stream_answer,
)

router = APIRouter()


# --------------------------------------------------
# DB dependency
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Request schema
# --------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    k: int = 5
    conversation_id: int | None = None


# --------------------------------------------------
# Citations helpers
# --------------------------------------------------
def build_sources_and_contexts(docs):
    """
    Stable numbering for citations:
    [1] (source.pdf)
    chunk text...
    """
    sources = []
    seen = set()

    for d in docs:
        src = d.get("source", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append(src)

    source_index = {src: i + 1 for i, src in enumerate(sources)}

    contexts = []
    for d in docs:
        src = d.get("source", "unknown")
        idx = source_index.get(src, 0)
        contexts.append(f"[{idx}] ({src})\n{d['text']}")

    return sources, contexts


# --------------------------------------------------
# NON-STREAMING QUERY
# --------------------------------------------------
@router.post("/query")
async def query(req: QueryRequest, db: Session = Depends(get_db)):

    conversation = None
    if req.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id)
            .first()
        )

    if conversation is None:
        conversation = crud_messages.create_conversation(db)

    conversation_id = conversation.id

    # store user message
    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=req.query,
    )

    history = crud_messages.get_recent_messages(db, conversation_id, limit=10)
    history_pairs = [(m.role, m.content) for m in history]

    # ✅ SINGLE retrieval strategy (evaluated)
    docs = hybrid_retrieve(
        req.query,
        conversation_id=conversation_id,
        k=req.k * 4,
        alpha=0.5,
    )

    if not docs:
        answer = "I don't have enough information in the provided documents."
        sources = []
    else:
        sources, contexts = build_sources_and_contexts(docs)
        answer = generate_answer_with_history(
            req.query,
            contexts,
            history_pairs,
        )

    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        meta={"sources": sources},
    )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
    }


# --------------------------------------------------
# STREAMING QUERY (ABORT-SAFE)
# --------------------------------------------------
@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    request: Request,
    db: Session = Depends(get_db),
):

    conversation = None
    if req.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id)
            .first()
        )

    if conversation is None:
        conversation = crud_messages.create_conversation(db)

    conversation_id = conversation.id

    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=req.query,
    )

    history = crud_messages.get_recent_messages(db, conversation_id, limit=10)
    history_pairs = [(m.role, m.content) for m in history]

    docs = hybrid_retrieve(
        req.query,
        conversation_id=conversation_id,
        k=req.k * 4,
        alpha=0.5,
    )

    sources, contexts = build_sources_and_contexts(docs)

    def event_stream():
        full_answer = ""

        for token in stream_answer(req.query, contexts, history_pairs):
            if request.client is None:
                return
            full_answer += token
            yield token

        crud_messages.add_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=full_answer,
            meta={"sources": sources},
        )

    return StreamingResponse(event_stream(), media_type="text/plain")
