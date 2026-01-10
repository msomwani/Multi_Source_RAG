# backend/app/vectorstore/store.py

import chromadb
from app.config import settings

client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

_COLLECTION_NAME = "documents"


def get_collection():
    return client.get_or_create_collection(_COLLECTION_NAME)


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
        enriched_metadatas.append(m)

    ids = [
        f"{conversation_id}_{doc_id}_{i}"
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=enriched_metadatas,
    )


def search(query_embedding, k: int = 5):
    collection = get_collection()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )