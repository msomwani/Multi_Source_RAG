from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import crud_messages
from app.db.models import Conversation

from app.retrieval.multiquery import multiquery_search
from app.retrieval.rerank import rerank
from app.llm.answer_generator import (
    generate_answer_with_history,
    stream_answer,
)

import json
import re

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


# --------------------------------------------------
# TABLE INTENT + EXTRACTION
# --------------------------------------------------
def _explicit_table_request(query: str) -> bool:
    q = (query or "").lower().strip()

    # normalize: remove punctuation + normalize spaces
    q = re.sub(r"[^a-z0-9\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    # common typo fix
    q = q.replace("teh", "the")

    triggers = [
        "show table",
        "show the table",
        "show me table",
        "show me the table",
        "render table",
        "display table",
        "print table",
        "full table",
        "entire table",
        "complete table",
        "give me the table",
        "share the table",
    ]

    return any(t in q for t in triggers)


def extract_tables_from_docs(query: str, docs):
    """
    ✅ Returns structured tables ONLY if user explicitly asks.
    ✅ Decodes table JSON stored in Chroma metadata (string -> dict).
    """
    if not _explicit_table_request(query):
        return []

    tables = []
    seen = set()

    for d in docs:
        meta = d.get("meta") or {}

        if meta.get("type") != "table_row":
            continue

        table = meta.get("table")

        # table stored as JSON string -> decode
        if isinstance(table, str):
            try:
                table = json.loads(table)
            except Exception:
                table = None

        if not isinstance(table, dict):
            continue

        title = table.get("title", "")
        cols = tuple(table.get("columns", []) or [])
        fp = (title, cols)

        if fp in seen:
            continue

        seen.add(fp)
        tables.append(table)

    return tables


def build_sources_and_contexts(docs):
    """
    ✅ Stable numbering for citations:
      sources = ["a.pdf", "b.docx"]
      contexts = ["[1] (a.pdf) ...", "[2] (b.docx) ..."]
    """
    sources = []
    seen = set()

    for d in docs:
        s = d.get("source", "unknown")
        if s not in seen:
            seen.add(s)
            sources.append(s)

    source_index = {src: i + 1 for i, src in enumerate(sources)}

    contexts = []
    for d in docs:
        src = d.get("source", "unknown")
        idx = source_index.get(src, 0)
        contexts.append(f"[{idx}] ({src})\n{d['text']}")

    return sources, contexts


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
        answer = "I don't have enough information in the provided documents."
        sources = []
        tables = []
    else:
        sources, contexts = build_sources_and_contexts(docs)
        tables = extract_tables_from_docs(req.query, docs)

        # ✅ table request = do NOT use LLM
        if _explicit_table_request(req.query) and tables:
            answer = "Sure — here is the table from your document. [1]"
        elif _explicit_table_request(req.query) and not tables:
            answer = "I couldn't find a table in the retrieved documents."
        else:
            answer = generate_answer_with_history(
                req.query,
                contexts,  # ✅ numbered contexts for inline citations
                history_pairs,
            )

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

    sources, contexts = build_sources_and_contexts(docs)
    tables = extract_tables_from_docs(req.query, docs)

    # ✅ If user asked for table and we have it → short streamed answer only
    if _explicit_table_request(req.query) and tables:

        def event_stream():
            full_answer = "Sure — here is the table from your document. [1]"
            yield full_answer

            crud_messages.add_message(
                db,
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer,
                meta={"sources": sources, "tables": tables},
            )

        return StreamingResponse(event_stream(), media_type="text/plain")

    # ✅ If user asked for table but none found
    if _explicit_table_request(req.query) and not tables:

        def event_stream():
            full_answer = "I couldn't find a table in the retrieved documents."
            yield full_answer

            crud_messages.add_message(
                db,
                conversation_id=conversation_id,
                role="assistant",
                content=full_answer,
                meta={"sources": sources, "tables": []},
            )

        return StreamingResponse(event_stream(), media_type="text/plain")

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
            meta={"sources": sources, "tables": []},  # ✅ NO TABLES unless explicitly asked
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
    )
