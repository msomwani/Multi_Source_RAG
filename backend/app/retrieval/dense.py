from app.llm.embeddings import embed
from app.vectorstore.store import get_collection
from typing import List, Dict
import json


def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
    """
    Dense retrieval scoped to a conversation.
    Returns: [{text, source, score, meta}]
    score = chroma distance (lower is better)
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

        # ✅ decode structured table json stored in metadata (if any)
        if isinstance(meta.get("table"), str):
            try:
                meta["table"] = json.loads(meta["table"])
            except Exception:
                pass

        if isinstance(meta.get("table_json"), str):
            try:
                meta["table"] = json.loads(meta["table_json"])
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
