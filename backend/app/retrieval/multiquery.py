from app.retrieval.hybrid import hybrid_retrieve
from app.llm.utils import generate_query_variations


def multiquery_search(
    query: str,
    conversation_id: int,
    k: int = 10,
    num_queries: int = 3,
):
    variations = generate_query_variations(query, n=num_queries)

    # ✅ If variations fail, fall back to original query only
    all_queries = [query] + variations if variations else [query]

    results = []

    for q in all_queries:
        try:
            docs = hybrid_retrieve(
                q,
                conversation_id=conversation_id,
                k=k,
                alpha=0.5,
            )
            results.extend(docs)
        except Exception:
            continue

    # Deduplicate by exact text
    seen = set()
    unique = []
    for d in results:
        t = d.get("text", "")
        if t and t not in seen:
            seen.add(t)
            unique.append(d)

    return unique[: k * 4]
