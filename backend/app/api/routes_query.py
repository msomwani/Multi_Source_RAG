from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation

from app.retrieval.hybrid import hybrid_retrieve
from app.llm.answer_generator import stream_answer

router = APIRouter()

# --------------------------------------------------
# Retrieval constants (final evaluated values)
# --------------------------------------------------
RETRIEVAL_K = 20
HYBRID_ALPHA = 0.5

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
# Request schema (locked)
# --------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    conversation_id: int | None = None

# --------------------------------------------------
# Citation helpers (stable numbering)
# --------------------------------------------------
def build_sources_and_contexts(docs: list[dict]):
    if not docs:
        return [], []

    sources = []
    seen = set()

    for d in docs:
        src = d.get("source", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append(src)

    source_index = {src: i + 1 for i, src in enumerate(sources)}

    contexts = [
        f"[{source_index.get(d.get('source', 'unknown'))}] "
        f"({d.get('source', 'unknown')})\n{d['text']}"
        for d in docs
    ]

    return sources, contexts

# --------------------------------------------------
# STREAMING QUERY (PRIMARY & ONLY ENDPOINT)
# --------------------------------------------------
@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Load or create conversation
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == req.conversation_id)
        .first()
        if req.conversation_id is not None
        else None
    )

    if conversation is None:
        conversation = crud_messages.create_conversation(db)

    conversation_id = conversation.id

    # Store user message
    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=req.query,
    )

    history = crud_messages.get_recent_messages(
        db, conversation_id, limit=10
    )
    history_pairs = [(m.role, m.content) for m in history]

    # Final evaluated pipeline: hybrid retrieval only
    docs = hybrid_retrieve(
        req.query,
        conversation_id=conversation_id,
        k=RETRIEVAL_K,
        alpha=HYBRID_ALPHA,
    )

    # Handle empty retrieval case explicitly
    if not docs:
        def empty_stream():
            msg = "I don't have enough information in the provided documents."
            yield msg
            crud_messages.add_message(
                db,
                conversation_id=conversation_id,
                role="assistant",
                content=msg,
                meta={"sources": []},
            )

        return StreamingResponse(
            empty_stream(),
            media_type="text/plain",
        )

    sources, contexts = build_sources_and_contexts(docs)

    def event_stream():
        full_answer = ""

        for token in stream_answer(
            req.query,
            contexts,
            history_pairs,
        ):
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

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
    )
