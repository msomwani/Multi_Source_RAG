from typing import List, Dict
import json

from app.llm.embeddings import embed
from app.vectorstore.store import get_collection


def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
    """
    Dense retrieval scoped to a conversation.
    score = Chroma distance (lower is better)
    """

    collection = get_collection()

    existing = collection.get(
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas"],
    )

    if not existing.get("documents"):
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
        meta = meta or {}

        # Decode structured table JSON if stored as string
        if isinstance(meta.get("table"), str):
            try:
                meta["table"] = json.loads(meta["table"])
            except Exception:
                pass

        docs.append(
            {
                "text": text,
                "source": meta.get("source", "unknown"),
                "score": float(score),
                "meta": meta,
            }
        )

    return docs
