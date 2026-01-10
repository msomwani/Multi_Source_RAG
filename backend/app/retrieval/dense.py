from app.llm.embeddings import embed
from app.vectorstore.store import get_collection
from typing import List, Tuple


def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
    ) -> List[Tuple[str, float]]:
    """
    Dense vector retrieval scoped to a conversation.
    """

    collection = get_collection()

    data=collection.get(
        where={"conversation_id":conversation_id},
        include=["documents","embeddings"],
    )

    docs=data.get("documents",[])
    # No docs for this conversation
    if not docs:
        return []

    query_vec = embed([query])[0]

    res = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        where={"conversation_id": conversation_id},
    )

    return list(zip(res["documents"][0], res["distances"][0]))
