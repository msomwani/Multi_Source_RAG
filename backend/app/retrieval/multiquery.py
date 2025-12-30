from app.retrieval.hybrid import hybrid_search
from app.llm.utils import generate_query_variations


def multiquery_search(query:str,k:int=5,num_queries:int=3):
    variations=generate_query_variations(query,n=num_queries)
    all_queries=[query]+variations
    results=[]

    for q in all_queries:
        docs=hybrid_search(q,k=k)
        results.extend(docs)

    seen=set()
    unique=[]
    for doc in results:
        if doc not in seen:
            unique.append(doc)
            seen.add(doc)

    return unique[:k]
