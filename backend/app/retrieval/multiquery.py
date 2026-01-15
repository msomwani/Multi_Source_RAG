from app.retrieval.dense import dense_retrieve
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
        docs = dense_retrieve(
            q,
            conversation_id=conversation_id,
            k=k,
        )
        results.extend(docs)

    # Deduplicate by text
    seen = set()
    unique = []

    for d in results:
        if d["text"] not in seen:
            seen.add(d["text"])
            unique.append(d)

    return unique[:k]
