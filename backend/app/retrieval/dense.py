from app.llm.embeddings import embed
from app.vectorstore.store import get_collection
from typing import List, Dict
import json



def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
    

    collection = get_collection()

    # If no docs exist for this conversation, return empty
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
        # ✅ decode table json if present
        if isinstance(meta.get("table_json"), str):
            try:
                meta["table"] = json.loads(meta["table_json"])
            except Exception:
                meta["table"] = None
        
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
