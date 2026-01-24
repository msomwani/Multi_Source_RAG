from rank_bm25 import BM25Okapi
from app.vectorstore.store import get_collection
from app.llm.embeddings import embed

import numpy as np
import re
from typing import List, Tuple


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def simple_tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


# --------------------------------------------------
# BM25 (per conversation, lazy)
# --------------------------------------------------

def build_bm25_index(conversation_id: int):
    collection = get_collection()

    data = collection.get(
        where={"conversation_id": conversation_id},
        include=["documents"],
    )

    docs = data.get("documents", [])
    if not docs:
        return None, []

    tokenized = [simple_tokenize(d) for d in docs]
    return BM25Okapi(tokenized), docs


def bm25_search(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Tuple[str, float]]:
    bm25, docs = build_bm25_index(conversation_id)
    if bm25 is None:
        return []

    tokens = simple_tokenize(query)
    scores = bm25.get_scores(tokens)

    topk = np.argsort(scores)[::-1][:k]
    return [(docs[i], scores[i]) for i in topk]


# --------------------------------------------------
# Dense Search (conversation-isolated)
# --------------------------------------------------

def dense_search(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Tuple[str, float, dict]]:
    collection = get_collection()

    data = collection.get(
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas"],
    )

    if not data.get("documents"):
        return []

    query_vec = embed([query])[0]

    res = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas", "distances"],
    )

    return list(zip(res["documents"][0], res["distances"][0], res["metadatas"][0]))



# --------------------------------------------------
# Hybrid Search (BM25 + Dense)
# --------------------------------------------------

def hybrid_search(
    query: str,
    conversation_id: int,
    k: int = 5,
    alpha: float = 0.5,
):
    bm25_res = bm25_search(query, conversation_id, k * 2)
    dense_res = dense_search(query, conversation_id, k * 2)

    if not bm25_res and not dense_res:
        return []

    scores = {}

    # Normalize BM25
    if bm25_res:
        bm25_max = max(s for _, s in bm25_res) or 1
        for doc, score in bm25_res:
            scores[doc] = scores.get(doc, 0) + (1 - alpha) * (score / bm25_max)

    # Normalize dense (lower distance = better)
    if dense_res:
        dense_max = max(s for _, s in dense_res) or 1
        for doc, score in dense_res:
            scores[doc] = scores.get(doc, 0) + alpha * (1 - score / dense_max)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in ranked[:k]]
