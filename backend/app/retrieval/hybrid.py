from typing import List, Dict
import re
import numpy as np

from rank_bm25 import BM25Okapi

from app.vectorstore.store import get_collection
from app.llm.embeddings import embed


def simple_tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", (text or "").lower())


def build_bm25_index(conversation_id: int):
    """
    NOTE:
    BM25 index is rebuilt per query.
    This is intentionally left uncached for correctness.
    """
    collection = get_collection()

    data = collection.get(
        where={"conversation_id": conversation_id},
        include=["documents", "metadatas"],
    )

    docs = data.get("documents", [])
    metas = data.get("metadatas", [])

    if not docs:
        return None, [], []

    tokenized = [simple_tokenize(d) for d in docs]
    return BM25Okapi(tokenized), docs, metas


def bm25_retrieve(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
    bm25, docs, metas = build_bm25_index(conversation_id)
    if bm25 is None:
        return []

    tokens = simple_tokenize(query)
    scores = bm25.get_scores(tokens)

    topk = np.argsort(scores)[::-1][:k]

    out = []
    for i in topk:
        meta = metas[i] or {}
        out.append(
            {
                "text": docs[i],
                "source": meta.get("source", "unknown"),
                "score": float(scores[i]),  # higher is better
                "meta": meta,
            }
        )

    return out


def dense_retrieve_raw(
    query: str,
    conversation_id: int,
    k: int = 5,
) -> List[Dict]:
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

    out = []
    for text, meta, dist in zip(
        res["documents"][0],
        res["metadatas"][0],
        res["distances"][0],
    ):
        meta = meta or {}
        out.append(
            {
                "text": text,
                "source": meta.get("source", "unknown"),
                "score": float(dist),  # lower is better
                "meta": meta,
            }
        )

    return out


def hybrid_retrieve(
    query: str,
    conversation_id: int,
    k: int = 10,
    alpha: float = 0.5,
) -> List[Dict]:
    """
    Final evaluated retrieval strategy.
    Combines:
      - BM25 (lexical)
      - Dense embeddings
    """

    bm25_docs = bm25_retrieve(query, conversation_id, k=k * 2)
    dense_docs = dense_retrieve_raw(query, conversation_id, k=k * 2)

    if not bm25_docs and not dense_docs:
        return []

    bm25_scores = [d["score"] for d in bm25_docs] or [0.0]
    bm25_max = max(bm25_scores) or 1.0

    dense_dists = [d["score"] for d in dense_docs] or [1.0]
    dense_max = max(dense_dists) or 1.0

    merged: dict[str, dict] = {}

    def key(d):
        return d["text"]

    for d in bm25_docs:
        merged[key(d)] = {
            "text": d["text"],
            "source": d["source"],
            "meta": d["meta"],
            "hybrid_score": (1 - alpha) * (d["score"] / bm25_max),
        }

    for d in dense_docs:
        dense_sim = 1.0 - (d["score"] / dense_max)

        if key(d) not in merged:
            merged[key(d)] = {
                "text": d["text"],
                "source": d["source"],
                "meta": d["meta"],
                "hybrid_score": alpha * dense_sim,
            }
        else:
            merged[key(d)]["hybrid_score"] += alpha * dense_sim

    ranked = sorted(
        merged.values(),
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )

    return [
        {
            "text": r["text"],
            "source": r["source"],
            "score": float(r["hybrid_score"]),
            "meta": r["meta"],
        }
        for r in ranked[:k]
    ]
