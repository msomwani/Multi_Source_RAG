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


# @router.post("/query")
# async def query(req: QueryRequest, db: Session = Depends(get_db)):

    # --------------------------------------------------
    # Resolve / create conversation
    # --------------------------------------------------
    # conversation = None

    # if req.conversation_id is not None:
    #     conversation = (
    #         db.query(Conversation)
    #         .filter(Conversation.id == req.conversation_id)
    #         .first()
    #     )

    # if conversation is None:
    #     conversation = crud_messages.create_conversation(db)

    # conversation_id = conversation.id

    # # --------------------------------------------------
    # # Save user message
    # # --------------------------------------------------
    # crud_messages.add_message(
    #     db,
    #     conversation_id=conversation_id,
    #     role="user",
    #     content=req.query,
    #     metadata={"sources": list({d.get("source", "unknown") for d in docs})},
    # )

    # # --------------------------------------------------
    # # Load history
    # # --------------------------------------------------
    # history = crud_messages.get_recent_messages(
    #     db, conversation_id, limit=10
    # )
    # history_pairs = [(m.role, m.content) for m in history]

    # # --------------------------------------------------
    # # Retrieval + rerank (conversation scoped)
    # # --------------------------------------------------
    # candidates = multiquery_search(
    #     req.query,
    #     conversation_id=conversation_id,
    #     k=req.k * 4,
    # )

    # docs = rerank(req.query, candidates, top_k=req.k)

    # print("🔎 Retrieved docs count:", len(docs))
    # print("🔎 Retrieved docs preview:", docs[:1])

    # # --------------------------------------------------
    # # Generate answer (ONCE)
    # # --------------------------------------------------
    # if not docs:
    #     answer = "I don't have enough information in my documents to answer that."
    # else:
    #     answer = generate_answer_with_history(
    #         req.query,
    #         [d["text"] for d in docs],  # 🔑 ONLY TEXT goes to LLM
    #         history_pairs,
    #     )

    # # --------------------------------------------------
    # # Save assistant message
    # # --------------------------------------------------
    # crud_messages.add_message(
    #     db,
    #     conversation_id=conversation_id,
    #     role="assistant",
    #     content=answer,
    # )

    # # --------------------------------------------------
    # # Final response (STABLE CONTRACT)
    # # --------------------------------------------------
    # return {
    #     "conversation_id": conversation_id,  # 🔑 FIXES /undefined
    #     "answer": answer,
    #     "sources": list({d.get("source", "unknown") for d in docs}),
    # }
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
        answer = "I don't have enough information in my documents to answer that."
    else:
        answer = generate_answer_with_history(
            req.query,
            [d["text"] for d in docs],
            history_pairs,
        )

    sources = list({d["source"] for d in docs})

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
