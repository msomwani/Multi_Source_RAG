from sentence_transformers import CrossEncoder

model = CrossEncoder("mixedbread-ai/mxbai-rerank-xsmall-v1")


def rerank(
    query: str,
    docs: list,
    top_k: int = 5,
    max_per_source: int = 2,
):
    if not docs:
        print("🟡 RERANK: received empty docs")
        return []

    print("\n🔵 RERANK INPUT (raw docs):")
    for i, d in enumerate(docs[:5]):
        print(f"  [{i}] type={type(d)} value={d}")

    # ----------------------------
    # Normalize (BUT PRESERVE META)
    # ----------------------------
    normalized = []

    for d in docs:
        if not isinstance(d, dict):
            continue

        text = d.get("text")
        if not text:
            continue

        source = d.get("source") or "unknown"
        meta = d.get("meta") or {}

        # ✅ keep everything important
        normalized.append(
            {
                "text": text,
                "source": source,
                "meta": meta,  # ✅ REQUIRED for structured tables
            }
        )

    print("\n🟢 RERANK AFTER NORMALIZATION:")
    for i, d in enumerate(normalized[:5]):
        print(f"  [{i}] text_len={len(d['text'])} source={d['source']} meta_keys={list((d.get('meta') or {}).keys())}")

    if not normalized:
        return []

    # ----------------------------
    # Cross-encoder scoring
    # ----------------------------
    pairs = [(query, d["text"]) for d in normalized]
    scores = model.predict(pairs)

    scored_docs = []
    for d, score in zip(normalized, scores):
        scored_docs.append(
            {
                "text": d["text"],
                "source": d["source"],
                "score": float(score),
                "meta": d.get("meta") or {},  # ✅ keep meta even after scoring
            }
        )

    # ----------------------------
    # Sort by relevance
    # ----------------------------
    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    # ----------------------------
    # SOURCE-DIVERSE SELECTION
    # ----------------------------
    final_docs = []
    source_counts = {}

    for d in scored_docs:
        src = d["source"]
        count = source_counts.get(src, 0)

        if count >= max_per_source:
            continue

        final_docs.append(d)
        source_counts[src] = count + 1

        if len(final_docs) >= top_k:
            break

    print("\n🟣 RERANK OUTPUT (source-diverse):")
    for i, d in enumerate(final_docs):
        print(
            f"  [{i}] score={d['score']:.4f} source={d['source']} meta_type={(d.get('meta') or {}).get('type')}"
        )

    return final_docs
