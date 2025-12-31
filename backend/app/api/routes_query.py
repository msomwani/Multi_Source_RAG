# from fastapi import APIRouter
# from app.retrieval.dense import dense_retrieve
# from app.llm.answer_generator import generate_answer

# router=APIRouter()

# @router.post("/query")
# async def ask(query:str):
#     results=dense_retrieve(query)
#     contexts=results["documents"][0]
#     answer=generate_answer(query,contexts)

#     return{"answer":answer,"contexts":contexts}


# from app.retrieval.hybrid import hybrid_search
from app.retrieval.multiquery import multiquery_search
from app.llm.answer_generator import generate_answer_with_history
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import crud_messages

router=APIRouter()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

class QueryRequest(BaseModel):
    query:str
    k:int=5
    conversation_id:int|None=None


@router.post("/query")
async def query(req: QueryRequest,db:Session=Depends(get_db)):

    #create conversation if not provided
    if req.conversation_id is None:
        convo=crud_messages.create_conversation(db)
        conversation_id=convo.id
    else:
        conversation_id=req.conversation_id

    #save user message
    crud_messages.add_message(
        db,
        conversation_id,
        role="user",
        content=req.query
    )

    #fetch recent history
    history=crud_messages.get_recent_messages(db,conversation_id,limit=10)

    #convert to role/content pairs
    history_pairs=[
        (m.role,m.content) for m in history
    ]


    docs=multiquery_search(req.query,k=req.k)
    # answer=generate_answer(req.query,docs)
    answer=generate_answer_with_history(req.query,docs,history_pairs)

    crud_messages.add_message(
        db,
        conversation_id,
        role="assistant",
        content=answer
    )

    return {
        "conversation_id":conversation_id,
        "answer":answer,
        "contexts":docs
    }