from fastapi import APIRouter
from app.retrieval.dense import dense_retrieve
from app.llm.answer_generator import generate_answer

router=APIRouter()

@router.post("/query")
async def ask(query:str):
    results=dense_retrieve(query)
    contexts=results["documents"][0]
    answer=generate_answer(query,contexts)

    return{"answer":answer,"contexts":contexts}