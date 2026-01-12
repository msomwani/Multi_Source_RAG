from app.retrieval.hybrid import hybrid_search
from app.llm.utils import generate_query_variations

def multiquery_search(
    query: str,
    conversation_id: int,
    k: int = 5,
    num_queries: int = 3,
):
    variations = generate_query_variations(query, n=num_queries)
    all_queries = [query] + variations

    results = []
    for q in all_queries:
        docs = hybrid_search(q, conversation_id, k)
        results.extend(docs)

    seen = set()
    unique = []
    for d in results:
        if d not in seen:
            unique.append(d)
            seen.add(d)

    return unique[:k]
