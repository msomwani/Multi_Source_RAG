from app.llm.embeddings import embed
from app.vectorstore.store import search

def dense_retrieve(query:str,k:int=5):
    """Enbed a query """
    query_vec=embed([query])[0]
    return search(query_vec,k)