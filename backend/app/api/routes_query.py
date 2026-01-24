from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation
import json

from app.retrieval.multiquery import multiquery_search
from app.retrieval.rerank import rerank
from app.llm.answer_generator import (
    generate_answer_with_history,
    stream_answer,
)

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

def extract_tables_from_docs(docs):
    """
    ✅ Collect structured tables from reranked docs metadata.
    Supports:
      meta["table"] as dict
      meta["table"] as JSON string
      meta["table_json"] as JSON string
    """

    tables = []
    seen = set()

    for d in docs:
        meta = d.get("meta") or {}
        if meta.get("type") != "table_row":
            continue

        table = meta.get("table")

        # ✅ if table is stored as string, decode it
        if isinstance(table, str):
            try:
                table = json.loads(table)
            except Exception:
                table = None

        # ✅ fallback: check table_json
        if table is None and isinstance(meta.get("table_json"), str):
            try:
                table = json.loads(meta["table_json"])
            except Exception:
                table = None

        if not isinstance(table, dict):
            continue

        # ✅ stable fingerprint (dedupe)
        title = table.get("title", "")
        cols = tuple(table.get("columns", []) or [])
        fp = (title, cols)

        if fp in seen:
            continue

        seen.add(fp)
        tables.append(table)

    return tables



# --------------------------------------------------
# NON-STREAMING
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

    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=req.query,
    )

    history = crud_messages.get_recent_messages(db, conversation_id, limit=10)
    history_pairs = [(m.role, m.content) for m in history]

    candidates = multiquery_search(
        req.query,
        conversation_id=conversation_id,
        k=req.k * 4,
    )

    docs = rerank(req.query, candidates, top_k=req.k)

    if not docs:
        answer = "I don't have enough information to answer that."
        sources = []
        tables = []
    else:
        answer = generate_answer_with_history(
            req.query,
            [d["text"] for d in docs],
            history_pairs,
        )
        sources = list({d.get("source", "unknown") for d in docs})
        tables = extract_tables_from_docs(docs)

    crud_messages.add_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        meta={"sources": sources, "tables": tables},
    )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
        "tables": tables,
    }


# --------------------------------------------------
# STREAMING (ABORT-SAFE)
# --------------------------------------------------
@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    request: Request,
    db: Session = Depends(get_db)
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

    candidates = multiquery_search(
        req.query,
        conversation_id=conversation_id,
        k=req.k * 4,
    )

    docs = rerank(req.query, candidates, top_k=req.k)

    contexts = [d["text"] for d in docs]
    sources = list({d.get("source", "unknown") for d in docs})

    # ✅ NEW: structured tables extracted from retrieved docs
    tables = extract_tables_from_docs(docs)

    def event_stream():
        full_answer = ""

        for token in stream_answer(req.query, contexts, history_pairs):
            if request.client is None:
                return

            full_answer += token
            yield token

        # ✅ save ONLY if completed
        crud_messages.add_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=full_answer,
            meta={"sources": sources, "tables": tables},
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
    )
