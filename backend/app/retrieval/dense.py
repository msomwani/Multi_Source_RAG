from app.llm.embeddings import embed
from app.vectorstore.store import get_collection
from typing import List, Dict


def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
    """
    Dense retrieval scoped to a conversation.
    Returns: [{text, source, score}]
    """

    collection = get_collection()

    # If no docs exist for this conversation, return empty
    existing = collection.get(
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas"],
    )

    if not existing["documents"]:
        return []

    query_vec = embed([query])[0]

    res = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas", "distances"],
    )

    docs = []
    for text, meta, score in zip(
        res["documents"][0],
        res["metadatas"][0],
        res["distances"][0],
    ):
        docs.append({
            "text": text,
            "source": meta.get("source", "unknown"),
            "score": float(score),
        })

    return docs
