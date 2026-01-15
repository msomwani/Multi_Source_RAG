from sentence_transformers import CrossEncoder

model = CrossEncoder("mixedbread-ai/mxbai-rerank-xsmall-v1")


def rerank(query: str, docs: list, top_k: int = 5):
    if not docs:
        print("🟡 RERANK: received empty docs")
        return []

    print("\n🔵 RERANK INPUT (raw docs):")
    for i, d in enumerate(docs[:5]):
        print(f"  [{i}] type={type(d)} value={d}")

    normalized = []

    for d in docs:
        if not isinstance(d, dict):
            continue

        text = d.get("text")
        source = d.get("source")  # 🔑 THIS IS THE KEY FIX

        if not text:
            continue

        normalized.append({
            "text": text,
            "source": source or "unknown",
        })

    print("\n🟢 RERANK AFTER NORMALIZATION:")
    for i, d in enumerate(normalized[:5]):
        print(f"  [{i}] text_len={len(d['text'])} source={d['source']}")

    if not normalized:
        return []

    pairs = [(query, d["text"]) for d in normalized]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(normalized, scores),
        key=lambda x: float(x[1]),
        reverse=True
    )[:top_k]

    output = [
        {
            "text": doc["text"],
            "source": doc["source"],   # ✅ WILL NEVER BE NONE
            "score": float(score),
        }
        for doc, score in ranked
    ]

    print("\n🟣 RERANK OUTPUT:")
    for i, d in enumerate(output):
        print(f"  [{i}] score={d['score']:.4f} source={d['source']}")

    return output
