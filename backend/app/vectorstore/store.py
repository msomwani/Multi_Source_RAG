# backend/app/vectorstore/store.py

import json
import chromadb
from app.config import settings

client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

_COLLECTION_NAME = "documents"


def get_collection():
    return client.get_or_create_collection(_COLLECTION_NAME)


def _sanitize_metadata_value(v):
    """
    Chroma only allows: str/int/float/bool/None
    If dict/list appears, convert to JSON string.
    """
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    # fallback: convert anything else to string
    return str(v)


def add_chunks(
    doc_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    conversation_id: int,
):
    """
    Store chunks in Chroma, isolated by conversation_id
    """

    collection = get_collection()

    enriched_metadatas = []
    for m in metadatas:
        m = dict(m)
        m["conversation_id"] = conversation_id

        # ✅ sanitize all keys
        clean_meta = {}
        for k, v in m.items():
            clean_meta[k] = _sanitize_metadata_value(v)

        enriched_metadatas.append(clean_meta)

    ids = [f"{conversation_id}_{doc_id}_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=enriched_metadatas,
    )


def search(query_embedding, conversation_id: int, k: int = 5):
    collection = get_collection()

    res = collection.query(
        query_embeddings=[query_embedding],
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

        docs.append(
            {
                "text": text,
                "source": meta.get("source", "unknown"),
                "score": float(score),
                "meta": meta,  # ✅ keep meta
            }
        )

    return docs
