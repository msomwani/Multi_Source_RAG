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


from app.retrieval.hybrid import hybrid_search
from app.llm.answer_generator import generate_answer
from fastapi import APIRouter
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query:str
    k:int=5

router=APIRouter()

@router.post("/query")
async def query(req: QueryRequest):
    docs=hybrid_search(req.query,k=req.k)
    answer=generate_answer(req.query,docs)

    return {
        "answer":answer,
        "contexts":docs
    }