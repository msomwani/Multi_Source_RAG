import json
import chromadb
from app.config import settings

client = chromadb.PersistentClient(
    path=settings.CHROMA_DB_PATH
)

_COLLECTION_NAME = "documents"


def get_collection():
    return client.get_or_create_collection(_COLLECTION_NAME)


def _sanitize_metadata_value(v):
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def add_chunks(
    doc_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    conversation_id: int,
):
    if not chunks:
        return

    collection = get_collection()

    enriched_metadatas = []
    for m in metadatas:
        m = dict(m)
        m["conversation_id"] = conversation_id
        clean_meta = {k: _sanitize_metadata_value(v) for k, v in m.items()}
        enriched_metadatas.append(clean_meta)

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
